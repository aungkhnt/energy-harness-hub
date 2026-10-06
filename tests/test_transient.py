import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from engine.runner import ROOT
from engine.transient import run_transient
from engine.network import run_network
from engine.numerics import ConvergenceError


def rc():
    return json.loads((ROOT/'scenarios/rc_charging.json').read_text())


class TransientTests(unittest.TestCase):
    def test_initial_conditions_and_analytic_rc_convergence(self):
        spec=rc(); exact=10*(1-math.exp(-5))
        coarse=run_transient(spec)
        spec['time']['step_s']/=2; fine=run_transient(spec)
        self.assertEqual(coarse['samples'][0]['node_voltages_v']['storage'],0)
        self.assertAlmostEqual(coarse['samples'][0]['branches'][-1]['current_a'],1)
        e1=abs(coarse['samples'][-1]['node_voltages_v']['storage']-exact)
        e2=abs(fine['samples'][-1]['node_voltages_v']['storage']-exact)
        self.assertLess(e2,e1*.6)
        self.assertLess(e2,.01)
        self.assertLess(fine['energy_accounting']['numerical_damping_j'],coarse['energy_accounting']['numerical_damping_j'])

    def test_discrete_energy_balance_separates_numerical_loss(self):
        result=run_transient(rc()); e=result['energy_accounting']
        self.assertAlmostEqual(e['net_input_to_storage_j'],e['final_stored_energy_j']-e['initial_stored_energy_j']+e['numerical_damping_j'],places=10)
        self.assertGreater(e['numerical_damping_j'],0)
        self.assertGreater(e['noncapacitor_absorbed_energy_j']['resistor'],0)
        self.assertLess(e['noncapacitor_absorbed_energy_j']['source'],0)
        self.assertLess(e['maximum_step_balance_residual_j'],1e-10)

    def test_discharge_and_nonzero_initial_state(self):
        spec=rc(); spec['network']['nodes']=['ground','storage']
        spec['network']['modules']=spec['network']['modules'][1:]
        spec['network']['modules'][0]['positive']='storage'
        spec['network']['modules'][0]['negative']='ground'
        spec['network']['modules'][1]['parameters']['initial_voltage_v']=10
        result=run_transient(spec)
        self.assertAlmostEqual(result['energy_accounting']['initial_stored_energy_j'],.5)
        self.assertLess(result['samples'][-1]['node_voltages_v']['storage'],.1)
        self.assertLess(result['energy_accounting']['net_input_to_storage_j'],0)

    def test_constant_current_ramp(self):
        spec=rc(); spec['time']={'duration_s':.1,'step_s':.01}
        spec['network']['nodes']=['ground','storage']
        cap=spec['network']['modules'][-1]
        spec['network']['modules']=[{'id':'source','type':'current_source','positive':'ground','negative':'storage','parameters':{'current_a':2}},cap]
        result=run_transient(spec)
        for sample in result['samples']:
            self.assertAlmostEqual(sample['node_voltages_v']['storage'],200*sample['time_s'],places=10)
        self.assertAlmostEqual(result['energy_accounting']['final_stored_energy_j'],2)

    def test_isolated_charged_capacitor_holds_state(self):
        spec=rc(); spec['network']['nodes']=['ground','storage']; spec['network']['modules']=spec['network']['modules'][-1:]
        spec['network']['modules'][0]['parameters']['initial_voltage_v']=3
        result=run_transient(spec)
        self.assertAlmostEqual(result['samples'][-1]['node_voltages_v']['storage'],3)
        self.assertAlmostEqual(result['energy_accounting']['numerical_damping_j'],0)

    def test_capacitor_between_nonreference_nodes(self):
        spec=rc(); spec['network']['modules'][-1]['positive']='supply'
        spec['network']['modules'][-1]['negative']='storage'
        result=run_transient(spec)
        self.assertAlmostEqual(result['samples'][0]['node_voltages_v']['storage'],10)
        self.assertAlmostEqual(result['samples'][-1]['total_stored_energy_j'],0)

    def test_initial_voltage_conflict_or_redundancy_rejected(self):
        for initial in (0,10):
            spec=rc(); spec['network']['modules'][-1]['positive']='supply'
            spec['network']['modules'][-1]['parameters']['initial_voltage_v']=initial
            with self.assertRaisesRegex(ConvergenceError,'Initial conditions'): run_transient(spec)

    def test_time_grid_ends_at_duration_and_preserves_input(self):
        spec=rc(); spec['time']={'duration_s':{'value':23,'unit':'ms'},'step_s':.01}
        before=copy.deepcopy(spec); result=run_transient(spec)
        self.assertEqual(result['time_grid']['step_count'],3)
        self.assertAlmostEqual(result['samples'][-1]['time_s'],.023)
        self.assertAlmostEqual(result['samples'][-1]['step']['dt_s'],.003)
        self.assertEqual(spec,before); self.assertEqual(result,run_transient(spec))

    def test_reject_invalid_controls_and_capacitance(self):
        for duration,step in [(0,.1),(.1,0),(.1,-1),(100,1e-9)]:
            spec=rc(); spec['time']={'duration_s':duration,'step_s':step}
            with self.assertRaises(ValueError): run_transient(spec)
        for capacitance in (0,-1,True,{'value':1,'unit':'W'}):
            spec=rc(); spec['network']['modules'][-1]['parameters']['capacitance_f']=capacitance
            with self.assertRaises(ValueError): run_transient(spec)

    def test_capacitor_not_silently_used_in_steady_solver(self):
        with self.assertRaisesRegex(ValueError,'transient'): run_network(rc()['network'])

    def test_no_state_is_rejected(self):
        spec=rc(); spec['network']['modules'].pop()
        with self.assertRaisesRegex(ValueError,'at least one capacitor'): run_transient(spec)

    def test_source_power_limit_applies_at_startup(self):
        spec=rc(); spec['network']['modules'][0]['parameters']['max_delivery_power_w']=5
        with self.assertRaisesRegex(ValueError,'delivery-power'): run_transient(spec)

    def test_tpv_startup_approaches_steady_and_refines(self):
        spec=json.loads((ROOT/'systems/tpv/scenarios/tpv_capacitor_startup.json').read_text())
        steady=copy.deepcopy(spec['network']); steady['modules'].pop()
        target=run_network(steady)['node_voltages_v']['load_bus']
        coarse=run_transient(spec); spec['time']['step_s']/=2; fine=run_transient(spec)
        self.assertEqual(coarse['samples'][0]['node_voltages_v']['load_bus'],0)
        self.assertAlmostEqual(fine['samples'][-1]['node_voltages_v']['load_bus'],target,places=4)
        self.assertLess(fine['energy_accounting']['numerical_damping_j'],coarse['energy_accounting']['numerical_damping_j'])
        self.assertLess(abs(fine['energy_accounting']['discrete_balance_residual_j']),1e-9)

    def test_cli_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'output'
            cmd=[sys.executable,'-m','engine','transient',str(ROOT/'scenarios/rc_charging.json'),'--output',str(output)]
            result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            saved=json.loads((output/'transient.json').read_text())
            self.assertEqual(saved['status'],'completed_transient_reference')
            self.assertTrue((output/'report.md').exists())
            self.assertEqual(subprocess.run(cmd,cwd=ROOT,capture_output=True).returncode,2)


if __name__=='__main__': unittest.main()
