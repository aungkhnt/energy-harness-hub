import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from engine.numerics import bisect, ConvergenceError
from engine.units import normalize
from engine.registry import get_model
from engine.runner import run, ROOT
from engine.studies import run_sweep, compare, comparison_markdown
from engine.contracts import validate_metrics


def hydro():
    return json.loads((ROOT/'systems/hydropower/scenarios/hydropower_reference.json').read_text())


def sweep():
    return {'schema_version':'0.1.0','study_id':'test-grid','base_study':hydro(),
            'axes':{'head_m':[5,10], 'flow_m3_s':[.1,.2]}}


class NumericsTests(unittest.TestCase):
    def test_root_against_analytic_answer(self):
        result=bisect(lambda x:x*x-2,0,2)
        self.assertAlmostEqual(result.root,math.sqrt(2),places=13)
        self.assertLessEqual(result.bracket_width,1e-14)
        self.assertGreater(result.iterations,0)

    def test_endpoint_and_decreasing_function(self):
        self.assertEqual(bisect(lambda x:x-2,2,3).root,2)
        self.assertAlmostEqual(bisect(lambda x:2-x,0,3).root,2)

    def test_bad_bracket_nonfinite_and_exhaustion(self):
        with self.assertRaises(ValueError): bisect(lambda x:x*x+1,-1,1)
        with self.assertRaises(ValueError): bisect(lambda x:float('nan'),0,1)
        with self.assertRaises(ConvergenceError): bisect(lambda x:x*x-2,0,2,max_iterations=1)


class UnitTests(unittest.TestCase):
    def test_conversions_and_affine_temperature(self):
        self.assertEqual(normalize({'value':20,'unit':'cm'},'m'),.2)
        self.assertAlmostEqual(normalize({'value':26.85,'unit':'degC'},'K'),300)
        self.assertEqual(normalize({'value':85,'unit':'%'},'1'),.85)
        self.assertEqual(normalize({'value':200,'unit':'L/s'},'m3/s'),.2)
        self.assertAlmostEqual(normalize({'value':1.602176634e-19,'unit':'J'},'eV'),1)

    def test_rejects_dimension_mismatch_and_bad_objects(self):
        for value in ({'value':1,'unit':'K'}, {'value':1,'unit':'watts'},
                      {'value':1,'unit':'m','extra':0}, True, float('inf')):
            with self.assertRaises(ValueError): normalize(value,'m')

    def test_equivalent_units_same_output_retained_provenance(self):
        original=hydro(); changed=copy.deepcopy(original)
        changed['parameters']['head_m']={'value':1000,'unit':'cm'}
        changed['parameters']['auxiliary_power_w']={'value':.2,'unit':'kW'}
        a,b=run(original),run(changed)
        self.assertEqual(a['metrics'],b['metrics'])
        self.assertEqual(b['normalized_parameters']['head_m'],10)
        self.assertNotEqual(a['input_sha256'],b['input_sha256'])
        self.assertIsInstance(b['input_snapshot']['parameters']['head_m'],dict)

    def test_describe_and_bad_model(self):
        definition=get_model('hydropower').describe()
        self.assertEqual(definition['parameter_units']['flow_m3_s'],'m3/s')
        with self.assertRaises(ValueError): get_model('not_implemented')


class BatchTests(unittest.TestCase):
    def test_cartesian_product_order_and_no_mutation(self):
        spec=sweep(); before=copy.deepcopy(spec)
        result=run_sweep(spec)
        self.assertEqual(spec,before)
        self.assertEqual(result['completed_count'],4)
        self.assertEqual([c['settings']['flow_m3_s'] for c in result['cases']],[.1,.1,.2,.2])
        self.assertEqual(result,run_sweep(spec))
        self.assertEqual(len({c['case_id'] for c in result['cases']}),4)

    def test_partial_failure_keeps_success_and_settings(self):
        spec=sweep(); spec['axes']={'head_m':[10,-1,20]}
        result=run_sweep(spec)
        self.assertEqual(result['status'],'partial_failure')
        self.assertEqual(result['completed_count'],2)
        self.assertEqual(result['cases'][1]['settings'],{'head_m':-1})
        self.assertNotIn('result',result['cases'][1])
        self.assertIn('error',result['cases'][1])

    def test_all_failed_and_bad_units(self):
        spec=sweep(); spec['axes']={'head_m':[{'value':1,'unit':'K'}]}
        self.assertEqual(run_sweep(spec)['status'],'failed')

    def test_invalid_base_contract_fails_before_execution(self):
        for key, value in [('schema_version','unsupported'),('assumptions',[])]:
            spec=sweep(); spec['base_study'][key]=value
            with self.assertRaises(ValueError): run_sweep(spec)

    def test_sweep_size_and_unknown_axis(self):
        spec=sweep(); spec['axes']={'head_m':list(range(300))}
        with self.assertRaisesRegex(ValueError,'limit'): run_sweep(spec)
        spec['axes']={'bad_parameter':[1]}
        with self.assertRaisesRegex(ValueError,'Unknown'): run_sweep(spec)

    def test_cli_partial_failure_saves_report(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory); spec=sweep(); spec['axes']={'head_m':[10,-1]}
            (folder/'input.json').write_text(json.dumps(spec))
            result=subprocess.run([sys.executable,'-m','engine','sweep',str(folder/'input.json'),
                                   '--output',str(folder/'output')],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,1,result.stderr)
            self.assertTrue((folder/'output/report.md').exists())
            self.assertEqual(json.loads((folder/'output/batch.json').read_text())['failed_count'],1)


class ComparisonTests(unittest.TestCase):
    def results(self):
        spec=hydro(); first=run(spec); spec['parameters']['head_m']=20
        return [first,run(spec)]

    def test_table_and_null_values(self):
        values=self.results()
        for result in values:
            result['metrics']['example']={'value':None,'unit':'W','scope':'test','status':'undefined_test'}
        table=compare(values,['net_electric_power','example'])
        self.assertIn('undefined',comparison_markdown(table))
        self.assertEqual(table['comparison_kind'],'within_model_operating_points')

    def test_rejects_mismatched_scope_unit_version_or_missing_metric(self):
        for field,value in [('scope','another scope'),('unit','kW')]:
            results=self.results(); results[1]['metrics']['net_electric_power'][field]=value
            with self.assertRaisesRegex(ValueError,'Incompatible'): compare(results,['net_electric_power'])
        for field in ('model_id','implementation_sha256'):
            results=self.results(); results[1][field]='different'
            with self.assertRaises(ValueError): compare(results,['net_electric_power'])
        with self.assertRaisesRegex(ValueError,'Missing'): compare(self.results(),['absent'])

    def test_invalid_result_contract(self):
        for value in (float('nan'),True,None):
            with self.assertRaises(ValueError):
                validate_metrics({'power':{'value':value,'unit':'W','scope':'test'}})


if __name__=='__main__':
    unittest.main()
