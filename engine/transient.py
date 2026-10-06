"""Fixed-step backward Euler for small constant-source RC/TPV networks.

Initial capacitor voltages are constraints, not guessed steady-state values.
The same nonlinear terminal laws and per-state checks apply at every time step.
"""
import copy
import json
import math
from . import __version__
from .validation import exact_fields
from .physics import positive
from .units import normalize
from .network import assemble, solve_system, summarize_state, _identifier
from .numerics import ConvergenceError
from .runner import digest, implementation_digest

MAX_STEPS = 2000


def _terminals(system, module):
    return [(system['node_index'].get(module['positive']),1),
            (system['node_index'].get(module['negative']),-1)]


def _voltage(system, module, state):
    return sum(sign*state[index] for index,sign in _terminals(system,module) if index is not None)


def _initial_system(system, capacitors):
    """Add capacitor initial-voltage constraints with unknown initial currents."""
    result=copy.deepcopy(system)
    base_n=len(system['rhs']); count=len(capacitors)
    result['matrix']=[row+[0.0]*count for row in result['matrix']]
    result['matrix'] += [[0.0]*(base_n+count) for _ in capacitors]
    for offset,cap in enumerate(capacitors):
        row=base_n+offset
        for node,sign in _terminals(system,cap):
            if node is not None:
                result['matrix'][node][row]=sign
                result['matrix'][row][node]=sign
        result['rhs'].append(cap['parameters']['initial_voltage_v'])
        result['variables'].append({'id':'initial_current:'+cap['id'],'unit':'A'})
        result['equations'].append({'id':'initial_voltage:'+cap['id'],'residual_unit':'V'})
    return result


def _step_system(system, capacitors, previous, dt):
    result={**system,'matrix':[row[:] for row in system['matrix']],'rhs':system['rhs'][:]}
    for cap in capacitors:
        conductance=cap['parameters']['capacitance_f']/dt
        history=conductance*_voltage(system,cap,previous)
        for row,sign_r in _terminals(system,cap):
            if row is not None:
                result['rhs'][row]+=sign_r*history
                for col,sign_c in _terminals(system,cap):
                    if col is not None:
                        result['matrix'][row][col]+=sign_r*sign_c*conductance
    return result


def _solver_diagnostics(solution, nonlinear):
    if nonlinear:
        return {'scaled_residual':solution.scaled_residual,'iterations':solution.iterations,
                'backtracks':solution.backtracks}
    return {'relative_residual':solution.relative_residual,'minimum_scaled_pivot':solution.minimum_scaled_pivot}


def _sample(system, state, capacitors, currents, time, solver_diagnostics):
    voltage,branches,kcl,net,scale,relative=summarize_state(system,state,currents)
    energies={cap['id']:.5*cap['parameters']['capacitance_f']*_voltage(system,cap,state)**2 for cap in capacitors}
    if any(not math.isfinite(v) for v in energies.values()):
        raise ConvergenceError('Non-finite capacitor energy')
    return {'time_s':time,'node_voltages_v':voltage,'branches':branches,
            'capacitor_energy_j':energies,'total_stored_energy_j':math.fsum(energies.values()),
            'diagnostics':{'node_kcl_residuals_a':kcl,'power_balance_residual_w':net,
                           'power_balance_acceptance_threshold_w':1e-9+1e-9*scale,
                           'solver':solver_diagnostics}}


def run_transient(spec):
    exact_fields(spec,['schema_version','study_id','network','time'])
    if spec['schema_version']!='0.1.0' or not _identifier(spec['study_id']):
        raise ValueError('Transient study requires schema 0.1.0 and a valid study_id')
    exact_fields(spec['time'],['duration_s','step_s'])
    duration=normalize(spec['time']['duration_s'],'s')
    step=normalize(spec['time']['step_s'],'s')
    positive('duration_s',duration); positive('step_s',step)
    ratio=duration/step
    if not math.isfinite(ratio) or ratio>MAX_STEPS+1e-9:
        raise ValueError(f'Transient study exceeds {MAX_STEPS} steps')
    nearest=round(ratio)
    count=max(1,nearest if math.isclose(ratio,nearest,rel_tol=1e-12,abs_tol=1e-12) else math.ceil(ratio))
    snapshot=json.loads(json.dumps(spec,allow_nan=False))
    system=assemble(snapshot['network'],allow_capacitors=True)
    capacitors=[m for m in system['modules'] if m['type']=='capacitor']
    if not capacitors:
        raise ValueError('Transient study requires at least one capacitor with an initial voltage')
    initial_system=_initial_system(system,capacitors)
    try:
        solution,nonlinear,_,_=solve_system(initial_system)
    except ConvergenceError as error:
        raise ConvergenceError('Initial conditions are inconsistent, underdetermined, or unsupported by the initial-constraint solver: '+str(error)) from error
    n=len(system['rhs']); state=solution.solution[:n]
    currents={cap['id']:solution.solution[n+i] for i,cap in enumerate(capacitors)}
    samples=[_sample(system,state,capacitors,currents,0.0,_solver_diagnostics(solution,nonlinear))]
    branch_energy={m['id']:0.0 for m in system['modules'] if m['type']!='capacitor'}
    damping=0.0; maximum_step_residual=0.0
    for index in range(1,count+1):
        time=duration if index==count else min(index*step,duration)
        dt=time-samples[-1]['time_s']
        if dt<=0:
            raise ValueError('Time grid is not representable as strictly increasing floats')
        discretized=_step_system(system,capacitors,state,dt)
        try:
            solved,nonlinear,_,_=solve_system(discretized,initial=state)
            new_state=solved.solution
            currents={cap['id']:cap['parameters']['capacitance_f']*(
                _voltage(system,cap,new_state)-_voltage(system,cap,state))/dt for cap in capacitors}
            sample=_sample(system,new_state,capacitors,currents,time,_solver_diagnostics(solved,nonlinear))
        except (ValueError,OverflowError,ZeroDivisionError) as error:
            raise ConvergenceError(f'Transient step {index} at t={time:g} s failed: {error}') from error
        step_damping=math.fsum(.5*cap['parameters']['capacitance_f']*(
            _voltage(system,cap,new_state)-_voltage(system,cap,state))**2 for cap in capacitors)
        transfers={b['id']:b['absorbed_power_w']*dt for b in sample['branches'] if b['type']!='capacitor'}
        energy_change=sample['total_stored_energy_j']-samples[-1]['total_stored_energy_j']
        residual=-math.fsum(transfers.values())-energy_change-step_damping
        energy_scale=math.fsum(abs(v) for v in transfers.values())+abs(energy_change)+step_damping
        if abs(residual)>1e-9+1e-8*energy_scale:
            raise ConvergenceError(f'Transient step {index} discrete energy balance exceeded tolerance')
        for key,value in transfers.items(): branch_energy[key]+=value
        damping+=step_damping
        maximum_step_residual=max(maximum_step_residual,abs(residual))
        sample['step']={'dt_s':dt,'stored_energy_change_j':energy_change,
                        'numerical_damping_j':step_damping,'discrete_energy_residual_j':residual}
        samples.append(sample); state=new_state
    initial_energy=samples[0]['total_stored_energy_j']; final_energy=samples[-1]['total_stored_energy_j']
    net_input=-math.fsum(branch_energy.values())
    result={'schema_version':'0.1.0','engine_version':__version__,'study_id':spec['study_id'],
            'status':'completed_transient_reference','execution_mode':'backward_euler',
            'input_snapshot':snapshot,'input_sha256':digest(snapshot),'implementation_sha256':implementation_digest(),
            'normalized_modules':system['modules'],
            'time_grid':{'duration_s':duration,'requested_step_s':step,'step_count':count,'sample_count':len(samples)},
            'state_definition':[{'id':cap['id'],'quantity':'terminal_voltage','unit':'V',
                'positive':cap['positive'],'negative':cap['negative'],
                'initial_voltage_v':cap['parameters']['initial_voltage_v']} for cap in capacitors],
            'equation_system':{'variables':system['variables'],'equations':system['equations'],
                'static_matrix':system['matrix'],'static_rhs':system['rhs'],
                'interpretation':'Static KCL + TPV terminal currents + capacitor currents C*(Vnew - Vold)/dt = 0. Capacitor parameters and TPV laws are in normalized_modules.'},
            'solver':{'integration':'fixed_step_backward_euler','initialization':'explicit capacitor voltage constraints',
                'warm_start':'previous solved electrical state','network_options':system['solver'],
                'accuracy_estimate':'not_estimated; compare refined time steps'},
            'samples':samples,
            'energy_accounting':{'quadrature':'right endpoint, consistent with backward Euler',
                'noncapacitor_absorbed_energy_j':branch_energy,'net_input_to_storage_j':net_input,
                'initial_stored_energy_j':initial_energy,'final_stored_energy_j':final_energy,
                'numerical_damping_j':damping,
                'discrete_balance_residual_j':net_input-(final_energy-initial_energy)-damping,
                'maximum_step_balance_residual_j':maximum_step_residual},
            'warnings':['Fixed sources and fixed-temperature TPV only; no switching events, inductors, controllers or thermal dynamics.',
                'Backward Euler is first order and numerically dissipative. Numerical damping is not physical heat or a device loss.',
                'A converged algebraic solve and a closed discrete energy budget do not certify time-integration accuracy; refine the time step.',
                'Initial capacitor constraints must admit a unique supported initialization; ideal voltage-source/capacitor loops may be rejected even when their voltages are consistent.',
                'The t=0 sample is a solved right-hand initial state, not a pre-switch state. No instantaneous impulses are modeled.']}
    if nonlinear:
        result['warnings'].append('TPV parameters are uncalibrated reference assumptions; generating-domain checks apply to every sample, with no implicit MPPT or conditioning.')
    json.dumps(result,allow_nan=False)
    return result


def transient_markdown(result):
    energy=result['energy_accounting']
    lines=['# '+result['study_id'],'','Fixed-step transient reference; see JSON for all samples and equations.','',
        f'Steps: {result["time_grid"]["step_count"]}; duration: {result["time_grid"]["duration_s"]:g} s.','',
        '| Quantity | Energy (J) |','|---|---:|']
    for key in ('initial_stored_energy_j','final_stored_energy_j','net_input_to_storage_j','numerical_damping_j','discrete_balance_residual_j'):
        lines.append(f'| {key} | {energy[key]:.9g} |')
    lines+=['','## Final node voltages','','| Node | V |','|---|---:|']
    lines += [f'| {node} | {v:.9g} |' for node,v in result['samples'][-1]['node_voltages_v'].items()]
    lines+=['','## Assumptions and limits','']
    lines+=['- '+w.replace('\n',' ') for w in result['input_snapshot']['network']['assumptions']+result['warnings']]
    lines+=['','Input hash: `'+result['input_sha256']+'`','',
            'Implementation hash: `'+result['implementation_sha256']+'`','']
    return '\n'.join(lines)
