"""Small steady DC networks assembled using modified nodal analysis.

Positive current runs from the positive terminal to the negative terminal;
positive branch power is absorbed. Reference node voltage is exactly zero.
"""
import json
import math
from . import __version__
from .validation import exact_fields
from .units import normalize
from .physics import positive
from .numerics import solve_linear, solve_nonlinear, ConvergenceError
from .terminals import prepare_tpv_terminal, tpv_current
from .runner import digest, implementation_digest

MODULES = {
    'capacitor': {'law':'I = C * d(Vpositive - Vnegative)/dt'},
    'tpv_cell': {'law':'Iabsorbed = I0 * expm1(V / Vthermal) - Iph'},
    'resistor': {'parameter':'resistance_ohm','unit':'ohm','law':'I = (Vp - Vn) / R'},
    'voltage_source': {'parameter':'voltage_v','unit':'V','law':'Vp - Vn = prescribed voltage'},
    'current_source': {'parameter':'current_a','unit':'A','law':'I = prescribed current from positive to negative terminal'},
}


def _identifier(value):
    return isinstance(value,str) and bool(value) and len(value)<=80 and all(c.isalnum() or c in '_-' for c in value)


def prepare_network(spec, *, allow_capacitors=False):
    exact_fields(spec,['schema_version','study_id','domain','nodes','reference_node','modules','assumptions'],['solver'])
    if spec['schema_version']!='0.1.0' or spec['domain']!='electrical_dc':
        raise ValueError('Network requires schema 0.1.0 and domain electrical_dc')
    if not _identifier(spec['study_id']):
        raise ValueError('Network study_id must be a short alphanumeric/hyphen/underscore identifier')
    nodes=spec['nodes']
    if not isinstance(nodes,list) or not 2 <= len(nodes) <= 64 or any(not _identifier(n) for n in nodes):
        raise ValueError('Network requires 2 to 64 valid node identifiers')
    if len(set(nodes))!=len(nodes) or spec['reference_node'] not in nodes:
        raise ValueError('Nodes must be unique and reference_node must exist')
    assumptions=spec['assumptions']
    if not isinstance(assumptions,list) or not assumptions or any(not isinstance(a,str) or not a.strip() for a in assumptions):
        raise ValueError('Network requires a nonempty list of assumptions')
    modules=spec['modules']
    if not isinstance(modules,list) or not 1 <= len(modules) <= 128:
        raise ValueError('Network requires 1 to 128 modules')
    normalized=[]; seen=set(); adjacency={n:set() for n in nodes}
    for module in modules:
        exact_fields(module,['id','type','positive','negative','parameters'])
        if not _identifier(module['id']) or module['id'] in seen:
            raise ValueError('Module identifiers must be valid and unique')
        seen.add(module['id'])
        kind=module['type']
        if not isinstance(kind,str) or kind not in MODULES:
            raise ValueError(f'Unsupported DC module type: {kind!r}')
        a,b=module['positive'],module['negative']
        if not isinstance(a,str) or not isinstance(b,str) or a not in nodes or b not in nodes or a==b:
            raise ValueError('Module terminals must reference two different existing nodes')
        if kind=='capacitor':
            if not allow_capacitors:
                raise ValueError('Capacitors require the transient command, not a steady network solve')
            exact_fields(module['parameters'],['capacitance_f','initial_voltage_v'])
            params={'capacitance_f':normalize(module['parameters']['capacitance_f'],'F'),
                    'initial_voltage_v':normalize(module['parameters']['initial_voltage_v'],'V')}
            positive('capacitance_f',params['capacitance_f'])
        elif kind=='tpv_cell':
            params=prepare_tpv_terminal(module['parameters'])
        else:
            info=MODULES[kind]; key=info['parameter']
            exact_fields(module['parameters'],[key],[] if kind=='resistor' else ['max_delivery_power_w'])
            params={key:normalize(module['parameters'][key],info['unit'])}
            if kind=='resistor':
                positive(key,params[key])
            elif 'max_delivery_power_w' in module['parameters']:
                cap=normalize(module['parameters']['max_delivery_power_w'],'W')
                positive('max_delivery_power_w',cap,allow_zero=True)
                params['max_delivery_power_w']=cap
        normalized.append({**module,'parameters':params})
        adjacency[a].add(b); adjacency[b].add(a)
    reached={spec['reference_node']}; pending=list(reached)
    while pending:
        for neighbor in adjacency[pending.pop()]-reached:
            reached.add(neighbor); pending.append(neighbor)
    if reached!=set(nodes):
        raise ValueError('Disconnected network: every node must connect to the reference node')
    options=spec.get('solver',{})
    exact_fields(options,[],['pivot_tolerance','residual_tolerance','nonlinear_tolerance','max_iterations','current_residual_scale_a','voltage_residual_scale_v'])
    if not any(m['type']=='tpv_cell' for m in normalized) and set(options)-{'pivot_tolerance','residual_tolerance'}:
        raise ValueError('Nonlinear solver options require a nonlinear module')
    # Ensure the snapshot is representable and detached from callers.
    snapshot=json.loads(json.dumps(spec,allow_nan=False))
    normalized=json.loads(json.dumps(normalized,allow_nan=False))
    return snapshot,normalized,dict(options)


def assemble(spec, *, allow_capacitors=False):
    """Return the inspectable linear equation system after topology validation."""
    snapshot,modules,options=prepare_network(spec,allow_capacitors=allow_capacitors)
    reference=spec['reference_node']
    active=[node for node in spec['nodes'] if node!=reference]
    sources=[m for m in modules if m['type']=='voltage_source']
    node_index={node:i for i,node in enumerate(active)}
    source_index={m['id']:len(active)+i for i,m in enumerate(sources)}
    variables=[{'id':'voltage:'+n,'unit':'V'} for n in active]+[{'id':'current:'+m['id'],'unit':'A'} for m in sources]
    equations=[{'id':'kcl:'+n,'residual_unit':'A'} for n in active]+[{'id':'voltage_law:'+m['id'],'residual_unit':'V'} for m in sources]
    n=len(variables); matrix=[[0.0]*n for _ in range(n)]; rhs=[0.0]*n
    for m in modules:
        p,q=node_index.get(m['positive']),node_index.get(m['negative'])
        if m['type']=='resistor':
            g=1/m['parameters']['resistance_ohm']
            for row,sign_r in ((p,1),(q,-1)):
                if row is not None:
                    for col,sign_c in ((p,1),(q,-1)):
                        if col is not None: matrix[row][col]+=sign_r*sign_c*g
        elif m['type']=='current_source':
            current=m['parameters']['current_a']
            if p is not None: rhs[p]-=current
            if q is not None: rhs[q]+=current
        elif m['type']=='voltage_source':
            i=source_index[m['id']]
            if p is not None: matrix[p][i]+=1; matrix[i][p]+=1
            if q is not None: matrix[q][i]-=1; matrix[i][q]-=1
            rhs[i]=m['parameters']['voltage_v']
    return {'snapshot':snapshot,'modules':modules,'solver':options,'variables':variables,
            'equations':equations,'matrix':matrix,'rhs':rhs,'node_index':node_index,
            'source_index':source_index}


def evaluate_network(system, state):
    """Evaluate physical residuals and their analytic Jacobian at a state."""
    residual=[math.fsum(a*x for a,x in zip(row,state))-b for row,b in zip(system['matrix'],system['rhs'])]
    jacobian=[row[:] for row in system['matrix']]
    for module in system['modules']:
        if module['type']!='tpv_cell':
            continue
        p=system['node_index'].get(module['positive'])
        q=system['node_index'].get(module['negative'])
        voltage=(state[p] if p is not None else 0)-(state[q] if q is not None else 0)
        current,slope=tpv_current(voltage,module['parameters'])
        for row,sign_r in ((p,1),(q,-1)):
            if row is not None:
                residual[row]+=sign_r*current
                for col,sign_c in ((p,1),(q,-1)):
                    if col is not None: jacobian[row][col]+=sign_r*sign_c*slope
    return residual,jacobian


def solve_system(system, initial=None):
    """Solve an assembled steady or discretized system; nonlinear steps may warm-start."""
    current_scale=voltage_scale=1.0
    nonlinear=any(m['type']=='tpv_cell' for m in system['modules'])
    if nonlinear:
        options=system['solver']
        if 'residual_tolerance' in options:
            raise ValueError('Use nonlinear_tolerance for nonlinear networks; residual_tolerance is linear-only')
        current_scale=options.get('current_residual_scale_a',1.0)
        voltage_scale=options.get('voltage_residual_scale_v',1.0)
        positive('current_residual_scale_a',current_scale)
        positive('voltage_residual_scale_v',voltage_scale)
        scales=[current_scale if eq['residual_unit']=='A' else voltage_scale for eq in system['equations']]
        solution=solve_nonlinear(lambda x:evaluate_network(system,x),
            [0.0]*len(scales) if initial is None else initial,scales,
            tolerance=options.get('nonlinear_tolerance',1e-10),
            max_iterations=options.get('max_iterations',100),
            pivot_tolerance=options.get('pivot_tolerance',1e-12))
    else:
        solution=solve_linear(system['matrix'],system['rhs'],**system['solver'])
    return solution,nonlinear,current_scale,voltage_scale


def summarize_state(system, state, capacitor_currents=None):
    """Physical branch results and conservation checks shared by both execution modes."""
    voltage={system['snapshot']['reference_node']:0.0}
    voltage.update({node:state[i] for node,i in system['node_index'].items()})
    branches=[]; kcl={node:0.0 for node in voltage}
    for m in system['modules']:
        dv=voltage[m['positive']]-voltage[m['negative']]
        if m['type']=='resistor': current=dv/m['parameters']['resistance_ohm']
        elif m['type']=='current_source': current=m['parameters']['current_a']
        elif m['type']=='capacitor':
            if capacitor_currents is None or m['id'] not in capacitor_currents:
                raise ValueError('Capacitor current required for transient state accounting')
            current=capacitor_currents[m['id']]
        elif m['type']=='tpv_cell':
            if not -1e-9 <= dv <= m['parameters']['open_circuit_voltage_v']+1e-9:
                raise ValueError(f'TPV cell {m["id"]} is outside the supported generating voltage range')
            current,_=tpv_current(dv,m['parameters'])
        else: current=state[system['source_index'][m['id']]]
        power=dv*current
        if not all(math.isfinite(v) for v in (dv,current,power)):
            raise ConvergenceError('Non-finite branch result')
        if m['type']=='tpv_cell' and -power > m['parameters']['maximum_dc_power_w']+1e-8:
            raise ConvergenceError('Solved TPV power exceeds its independently computed maximum power')
        cap=m['parameters'].get('max_delivery_power_w')
        if cap is not None and -power > cap+1e-10*max(1,cap):
            raise ValueError(f'Source {m["id"]} exceeds its specified delivery-power limit; no valid operating point under these assumptions')
        kcl[m['positive']]+=current; kcl[m['negative']]-=current
        branches.append({'id':m['id'],'type':m['type'],'positive':m['positive'],'negative':m['negative'],
                         'voltage_drop_v':dv,'current_a':current,'absorbed_power_w':power})
    net=math.fsum(b['absorbed_power_w'] for b in branches)
    scale=math.fsum(abs(b['absorbed_power_w']) for b in branches)
    relative=abs(net)/scale if scale else 0.0
    if abs(net)>1e-9+1e-9*scale:
        raise ConvergenceError('Network power conservation exceeds tolerance')
    return voltage,branches,kcl,net,scale,relative


def run_network(spec):
    system=assemble(spec)
    solution,nonlinear,current_scale,voltage_scale=solve_system(system)
    voltage,branches,kcl,net,scale,relative=summarize_state(system,solution.solution)
    result={'schema_version':'0.1.0','engine_version':__version__,
            'status':'completed_network_reference','study_id':spec['study_id'],
            'domain':'electrical_dc','execution_mode':'nonlinear_steady_state' if nonlinear else 'linear_steady_state',
            'input_snapshot':system['snapshot'],'normalized_modules':system['modules'],
            'input_sha256':digest(system['snapshot']),'implementation_sha256':implementation_digest(),
            'node_voltages_v':voltage,'branches':branches,
            'equation_system':{k:system[k] for k in ('variables','equations','matrix','rhs')},
            'diagnostics':{'linear_relative_residual':None if nonlinear else solution.relative_residual,
                           'minimum_scaled_pivot':None if nonlinear else solution.minimum_scaled_pivot,
                           'node_kcl_residuals_a':kcl,'power_balance_residual_w':net,
                           'relative_power_balance_residual':relative,
                           'power_balance_acceptance_threshold_w':1e-9+1e-9*scale,
                           'unknown_count':len(solution.solution),'equation_count':len(system['rhs'])},
            'solver':{'method':'row_scaled_partial_pivot_gaussian_elimination',
                      'pivot_tolerance':system['solver'].get('pivot_tolerance',1e-12),
                      'residual_tolerance':system['solver'].get('residual_tolerance',1e-10)},
            'warnings':['Steady DC network with ideal sources, resistors and optional ideal-diode TPV cells; no dynamics, AC or thermal coupling.',
                        'Positive branch current flows from positive to negative terminal; positive power is absorbed, negative power is delivered.',
                        'Ideal sources remain prescribed assumptions. tpv_cell modules derive a terminal law from the existing fixed-temperature TPV reference model; hydropower has no terminal adapter yet.',
                        'Optional source delivery limits reject infeasible results; no voltage droop, saturation or control law is modeled.',
                        'A small residual is not a condition-number estimate or empirical validation.']}
    if nonlinear:
        result['diagnostics'].update(nonlinear_scaled_residual=solution.scaled_residual,
                                     nonlinear_iterations=solution.iterations,line_search_backtracks=solution.backtracks)
        result['solver']={'method':'damped_newton_analytic_jacobian',
                          'nonlinear_tolerance':system['solver'].get('nonlinear_tolerance',1e-10),
                          'max_iterations':system['solver'].get('max_iterations',100),
                          'max_backtracks':40,
                          'pivot_tolerance':system['solver'].get('pivot_tolerance',1e-12),
                          'current_residual_scale_a':current_scale,'voltage_residual_scale_v':voltage_scale,
                          'initial_state':'all_zero'}
        result['equation_system']['nonlinear_terms']=[
            {'module_id':m['id'],'positive':m['positive'],'negative':m['negative'],
             'law':MODULES['tpv_cell']['law'],
             'parameters':{k:m['parameters'][k] for k in ('photocurrent_a','saturation_current_a','thermal_voltage_v')}}
             for m in system['modules'] if m['type']=='tpv_cell']
        result['equation_system']['interpretation']='Residual = matrix @ state - rhs + nonlinear terminal currents stamped into KCL rows.'
        result['tpv_operating_points']=[]
        for m,b in zip(system['modules'],branches):
            if m['type']=='tpv_cell':
                result['tpv_operating_points'].append({'module_id':m['id'],
                    'delivered_dc_power_w':-b['absorbed_power_w'],
                    'maximum_dc_power_w':m['parameters']['maximum_dc_power_w'],
                    'absorbed_radiation_power_w':m['parameters']['absorbed_radiation_power_w'],
                    'unresolved_nonelectrical_power_w':m['parameters']['absorbed_radiation_power_w']+b['absorbed_power_w']})
                result['warnings'].extend(m['parameters']['model_warnings'])
        result['warnings'].append('TPV output is raw cell DC at the load-selected operating point. No MPPT, power conditioner or auxiliary load is silently applied.')
    json.dumps(result,allow_nan=False)
    return result


def network_markdown(result):
    rows=['# '+result['study_id'],'','Steady DC network reference; ideal source/load assumptions.','',
          '| Node | Voltage (V) |','|---|---:|']
    rows += [f'| {node} | {voltage:.8g} |' for node,voltage in result['node_voltages_v'].items()]
    rows+=['','| Module | Voltage drop (V) | Current p→n (A) | Absorbed power (W) |','|---|---:|---:|---:|']
    rows += [f'| {b["id"]} | {b["voltage_drop_v"]:.8g} | {b["current_a"]:.8g} | {b["absorbed_power_w"]:.8g} |' for b in result['branches']]
    if result.get('tpv_operating_points'):
        rows+=['','## TPV operating points','','| Cell | Delivered DC (W) | Available MPP (W) | Absorbed radiation (W) |','|---|---:|---:|---:|']
        rows += [f'| {p["module_id"]} | {p["delivered_dc_power_w"]:.8g} | {p["maximum_dc_power_w"]:.8g} | {p["absorbed_radiation_power_w"]:.8g} |' for p in result['tpv_operating_points']]
    rows+=['','## Diagnostics','','```json',json.dumps(result['diagnostics'],indent=2),'```',
           '','## Assumptions and limits','']
    rows+=['- '+w.replace('\n',' ') for w in result['input_snapshot']['assumptions']+result['warnings']]
    rows+=['','The companion JSON preserves all equations, inputs, normalized modules, and source hashes.','']
    return '\n'.join(rows)
