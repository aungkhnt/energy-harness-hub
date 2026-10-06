import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from engine.numerics import solve_linear, ConvergenceError
from engine.network import assemble, run_network
from engine.runner import ROOT


def example():
    return json.loads((ROOT/'scenarios/dc_distribution.json').read_text())


class LinearTests(unittest.TestCase):
    def test_pivoting_and_input_not_mutated(self):
        matrix=[[0,2],[1,3]]; rhs=[4,7]; before=copy.deepcopy(matrix)
        result=solve_linear(matrix,rhs)
        self.assertAlmostEqual(result.solution[0],1,places=13)
        self.assertAlmostEqual(result.solution[1],2,places=13)
        self.assertEqual(matrix,before)
        self.assertLess(result.relative_residual,1e-12)

    def test_row_scaling(self):
        result=solve_linear([[1e-20,2e-20],[3e20,4e20]],[5e-20,11e20])
        self.assertAlmostEqual(result.solution[0],1)
        self.assertAlmostEqual(result.solution[1],2)

    def test_singular_and_inconsistent_rejected(self):
        for rhs in ([2,4],[2,5]):
            with self.assertRaises(ConvergenceError): solve_linear([[1,1],[2,2]],rhs)

    def test_invalid_shapes_and_nonfinite(self):
        for matrix,rhs in [([],[]),([[1,2]],[1]),([[float('nan')]],[1]),([[True]],[1])]:
            with self.assertRaises(ValueError): solve_linear(matrix,rhs)
        with self.assertRaises(ValueError): solve_linear([[1]],[1],pivot_tolerance=0)


class NetworkTests(unittest.TestCase):
    def test_parallel_loads_line_drop_and_power(self):
        result=run_network(example())
        # Independent series/parallel circuit reduction: 12 || 24 = 8 ohm.
        current=48/8.5
        self.assertAlmostEqual(result['node_voltages_v']['load_bus'],current*8)
        branches={b['id']:b for b in result['branches']}
        self.assertAlmostEqual(branches['supply']['current_a'],-current)
        self.assertAlmostEqual(branches['line']['absorbed_power_w'],current**2*.5)
        self.assertAlmostEqual(branches['load_two']['current_a'],current*8/24)
        self.assertLess(abs(result['diagnostics']['power_balance_residual_w']),1e-10)
        self.assertLess(max(abs(v) for v in result['diagnostics']['node_kcl_residuals_a'].values()),1e-12)

    def test_current_source_and_polarity(self):
        spec=example(); spec['nodes']=['ground','bus']; spec['modules']=[
            {'id':'injection','type':'current_source','positive':'ground','negative':'bus','parameters':{'current_a':{'value':2000,'unit':'mA'}}},
            {'id':'load','type':'resistor','positive':'bus','negative':'ground','parameters':{'resistance_ohm':10}}]
        result=run_network(spec)
        self.assertAlmostEqual(result['node_voltages_v']['bus'],20)
        self.assertAlmostEqual(result['branches'][0]['absorbed_power_w'],-40)

    def test_voltage_constraint_between_two_nonreference_nodes(self):
        spec=example(); spec['modules'][0]['negative']='load_bus'
        spec['modules'][0]['parameters'].pop('max_delivery_power_w')
        result=run_network(spec)
        self.assertAlmostEqual(result['node_voltages_v']['source_bus']-result['node_voltages_v']['load_bus'],48)
        self.assertAlmostEqual(result['node_voltages_v']['load_bus'],0)

    def test_equation_system_and_determinism(self):
        spec=example(); before=copy.deepcopy(spec); result=run_network(spec)
        self.assertEqual(spec,before)
        self.assertEqual(result,run_network(spec))
        self.assertEqual(len(result['equation_system']['variables']),3)
        self.assertEqual(result['normalized_modules'][-1]['parameters']['resistance_ohm'],24)

    def test_disconnected_and_unknown_nodes(self):
        spec=example(); spec['nodes'].append('floating')
        with self.assertRaisesRegex(ValueError,'Disconnected'): run_network(spec)
        spec=example(); spec['modules'][0]['positive']='unknown'
        with self.assertRaises(ValueError): run_network(spec)

    def test_connected_but_voltage_unconstrained(self):
        spec=example(); spec['nodes']=['ground','bus']; spec['modules']=[
            {'id':'injection','type':'current_source','positive':'ground','negative':'bus','parameters':{'current_a':1}}]
        with self.assertRaises(ConvergenceError): run_network(spec)

    def test_inconsistent_voltage_sources(self):
        spec=example(); other=copy.deepcopy(spec['modules'][0]); other['id']='second'
        other['parameters']['voltage_v']=40; spec['modules'].append(other)
        with self.assertRaises(ConvergenceError): run_network(spec)

    def test_rating_exceeded(self):
        spec=example(); spec['modules'][0]['parameters']['max_delivery_power_w']=100
        with self.assertRaisesRegex(ValueError,'delivery-power limit'): run_network(spec)

    def test_bad_parameters_domains_and_duplicate_ids(self):
        for mutation in ('unit','resistance','type','duplicate','domain'):
            spec=example()
            if mutation=='unit': spec['modules'][1]['parameters']['resistance_ohm']={'value':1,'unit':'W'}
            if mutation=='resistance': spec['modules'][1]['parameters']['resistance_ohm']=0
            if mutation=='type': spec['modules'][1]['type']='thermal_link'
            if mutation=='duplicate': spec['modules'][1]['id']='supply'
            if mutation=='domain': spec['domain']='thermal'
            with self.assertRaises(ValueError): assemble(spec)

    def test_cli_artifacts_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'network'
            cmd=[sys.executable,'-m','engine','network',str(ROOT/'scenarios/dc_distribution.json'),'--output',str(output)]
            completed=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(completed.returncode,0,completed.stderr)
            self.assertTrue((output/'report.md').exists())
            self.assertEqual(json.loads((output/'network.json').read_text())['status'],'completed_network_reference')
            again=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(again.returncode,2)


if __name__=='__main__':
    unittest.main()
