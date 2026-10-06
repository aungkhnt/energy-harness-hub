import copy
import json
import math
import unittest

from engine.numerics import solve_nonlinear, ConvergenceError, bisect
from engine.network import run_network, assemble, evaluate_network
from engine.runner import ROOT
from engine.terminals import prepare_tpv_terminal, tpv_current


def example():
    return json.loads((ROOT/'systems/tpv/scenarios/tpv_connected_load.json').read_text())


def direct_load(resistance):
    spec=example(); spec['nodes']=['ground','cell_bus']; spec['modules'].pop(1)
    spec['modules'][1]['positive']='cell_bus'
    spec['modules'][1]['parameters']['resistance_ohm']=resistance
    return spec


class NonlinearSolverTests(unittest.TestCase):
    def test_coupled_system(self):
        result=solve_nonlinear(lambda x:([x[0]**2+x[1]-3,x[0]+x[1]-2],
                                        [[2*x[0],1],[1,1]]),[2,0],[1,1])
        root=(1+math.sqrt(5))/2
        self.assertAlmostEqual(result.solution[0],root,places=9)
        self.assertAlmostEqual(result.solution[1],2-root,places=9)
        self.assertLessEqual(result.scaled_residual,1e-10)

    def test_backtracking_exponential(self):
        result=solve_nonlinear(lambda x:([math.exp(x[0])-10],[[math.exp(x[0])]]),[0],[1])
        self.assertAlmostEqual(result.solution[0],math.log(10),places=9)
        self.assertGreater(result.backtracks,0)

    def test_scaled_equations(self):
        result=solve_nonlinear(lambda x:([1e6*(x[0]**2-2)],[[2e6*x[0]]]),[1],[1e6])
        self.assertAlmostEqual(result.solution[0],math.sqrt(2),places=9)

    def test_failure_is_explicit(self):
        with self.assertRaises(ConvergenceError):
            solve_nonlinear(lambda x:([x[0]**2+1],[[2*x[0]]]),[1],[1])
        with self.assertRaises(ConvergenceError):
            solve_nonlinear(lambda x:([x[0]**2-2],[[2*x[0]]]),[10],[1],max_iterations=1)
        with self.assertRaises(ConvergenceError):
            solve_nonlinear(lambda x:([0],[[0]]),[0],[1])

    def test_invalid_controls(self):
        for options in ({'tolerance':0},{'max_iterations':True},{'max_backtracks':0}):
            with self.assertRaises(ValueError):
                solve_nonlinear(lambda x:([x[0]],[[1]]),[1],[1],**options)


class TPVNetworkTests(unittest.TestCase):
    def test_loaded_cell_against_scalar_load_line(self):
        spec=direct_load(.05)
        terminal=prepare_tpv_terminal(spec['modules'][0]['parameters'])
        expected=bisect(lambda v:tpv_current(v,terminal)[0]+v/.05,0,terminal['open_circuit_voltage_v']).root
        result=run_network(spec)
        self.assertAlmostEqual(result['node_voltages_v']['cell_bus'],expected,places=9)
        self.assertEqual(result['execution_mode'],'nonlinear_steady_state')
        self.assertLess(abs(result['diagnostics']['power_balance_residual_w']),1e-9)

    def test_analytic_jacobian_against_finite_difference(self):
        system=assemble(example()); state=[.3,.29]; _,jac=evaluate_network(system,state)
        for col in range(2):
            lo=state[:]; hi=state[:]; lo[col]-=1e-7; hi[col]+=1e-7
            f0,_=evaluate_network(system,lo); f1,_=evaluate_network(system,hi)
            for row in range(2):
                self.assertAlmostEqual(jac[row][col],(f1[row]-f0[row])/2e-7,places=5)

    def test_matched_load_recovers_mpp_and_mismatch_reduces_power(self):
        spec=direct_load(.05)
        terminal=prepare_tpv_terminal(spec['modules'][0]['parameters'])
        from engine.physics import diode_mpp, K, Q
        mpp=diode_mpp(terminal['photocurrent_a'],terminal['saturation_current_a'],terminal['thermal_voltage_v']*Q/K)
        matched=run_network(direct_load(mpp['vmpp_v']/mpp['impp_a']))
        power=matched['tpv_operating_points'][0]['delivered_dc_power_w']
        self.assertAlmostEqual(power,mpp['dc_power_w'],places=8)
        for resistance in (.001,1):
            other=run_network(direct_load(resistance))
            self.assertLess(other['tpv_operating_points'][0]['delivered_dc_power_w'],power)

    def test_open_and_short_circuit(self):
        spec=direct_load(.05); spec['modules'].pop()
        terminal=prepare_tpv_terminal(spec['modules'][0]['parameters'])
        result=run_network(spec)
        self.assertAlmostEqual(result['node_voltages_v']['cell_bus'],terminal['open_circuit_voltage_v'],places=8)
        self.assertLess(abs(result['tpv_operating_points'][0]['delivered_dc_power_w']),1e-9)
        spec['modules'].append({'id':'short','type':'voltage_source','positive':'cell_bus','negative':'ground','parameters':{'voltage_v':0}})
        result=run_network(spec)
        self.assertEqual(result['node_voltages_v']['cell_bus'],0)
        self.assertAlmostEqual(result['branches'][1]['current_a'],terminal['photocurrent_a'],places=8)

    def test_dark_cell_and_determinism(self):
        spec=direct_load(.05); spec['modules'][0]['parameters']['tpv_parameters']['emissivity']=0
        before=copy.deepcopy(spec); result=run_network(spec)
        self.assertEqual(result['node_voltages_v']['cell_bus'],0)
        self.assertEqual(result,run_network(spec)); self.assertEqual(spec,before)

    def test_outside_supported_quadrant_rejected(self):
        spec=direct_load(.05); spec['modules'][1]={'id':'reverse','type':'voltage_source','positive':'cell_bus','negative':'ground','parameters':{'voltage_v':-.1}}
        with self.assertRaisesRegex(ValueError,'generating voltage'): run_network(spec)

    def test_conditioning_and_wrong_solver_options_rejected(self):
        spec=example(); spec['modules'][0]['parameters']['tpv_parameters']['conditioning_efficiency']=.95
        with self.assertRaisesRegex(ValueError,'bare cell'): run_network(spec)
        spec=example(); spec['solver']={'residual_tolerance':1e-9}
        with self.assertRaisesRegex(ValueError,'nonlinear_tolerance'): run_network(spec)

    def test_line_loss_and_equations_saved(self):
        result=run_network(example()); branches={b['id']:b for b in result['branches']}
        self.assertAlmostEqual(-branches['cell']['absorbed_power_w'],branches['load']['absorbed_power_w']+branches['lead']['absorbed_power_w'],places=8)
        self.assertEqual(result['equation_system']['nonlinear_terms'][0]['module_id'],'cell')
        self.assertGreater(result['diagnostics']['nonlinear_iterations'],0)


if __name__=='__main__': unittest.main()
