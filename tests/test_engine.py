import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from engine.physics import (SIGMA, radiance, integrate_log, rectangle_coupling,
                            diode_mpp, K, Q)
from engine.runner import ROOT, run, catalog
from engine.economics import assess


def example(name):
    return json.loads((ROOT/'systems'/name/'scenarios'/f'{name}_reference.json').read_text())


class RadiationTests(unittest.TestCase):
    def test_planck_recovers_stefan_boltzmann(self):
        for temperature in (300, 1000, 2000, 4000):
            integral = math.pi*integrate_log(lambda w: radiance(w,temperature),1e-9,1e-2,2048)
            self.assertAlmostEqual(integral/(SIGMA*temperature**4),1,places=7)

    def test_spectrum_peak_matches_wien(self):
        # Independent displacement-law reference, not a second call to the same equation.
        for temperature in (1000,3000):
            peak=2.897771955e-3/temperature
            self.assertGreater(radiance(peak,temperature),radiance(.99*peak,temperature))
            self.assertGreater(radiance(peak,temperature),radiance(1.01*peak,temperature))

    def test_geometry_reciprocity_and_offset_symmetry(self):
        first=rectangle_coupling(.05,.03,.02,.01,.1,.02,-.01,cells=8)
        swapped=rectangle_coupling(.02,.01,.05,.03,.1,-.02,.01,cells=8)
        self.assertAlmostEqual(first,swapped,places=15)
        centered=rectangle_coupling(.05,.03,.02,.01,.1,cells=8)
        self.assertLess(first,centered)

    def test_far_field_limit(self):
        result=rectangle_coupling(.01,.02,.03,.04,10,cells=8)
        expected=(.01*.02)*(.03*.04)/10**2
        self.assertLess(abs(result/expected-1),1e-5)

    def test_grid_convergence(self):
        args=(.05,.04,.02,.01,.1)
        values=[rectangle_coupling(*args,cells=n) for n in (4,8,16,32)]
        self.assertLess(abs(values[2]-values[3]),abs(values[1]-values[3]))
        self.assertLess(abs(values[1]-values[3]),abs(values[0]-values[3]))

    def test_invalid_spectral_domain(self):
        for low,high,n in [(0,1,32),(1,.1,32),(.1,1,33)]:
            with self.assertRaises(ValueError):
                integrate_log(lambda w:w,low,high,n)


class ElectricalTests(unittest.TestCase):
    def test_mpp_stationary_and_better_than_neighbor(self):
        iph,i0,temp=2,.00001,300
        result=diode_mpp(iph,i0,temp)
        v=result['vmpp_v']; vt=K*temp/Q
        def power(voltage):
            return voltage*(iph-i0*math.expm1(voltage/vt))
        self.assertGreater(power(v),power(v*.999))
        self.assertGreater(power(v),power(v*1.001))
        derivative=iph-i0*math.expm1(v/vt)-v*i0*math.exp(v/vt)/vt
        self.assertAlmostEqual(derivative,0,places=12)
        self.assertAlmostEqual(result['iv_curve'][-1]['current_a'],0,places=12)

    def test_dark_cell(self):
        self.assertEqual(diode_mpp(0,.01,300)['dc_power_w'],0)

    def test_hydro_known_solution_and_negative_net(self):
        study=example('hydropower'); study.pop('economics')
        p=study['parameters']; p.update(head_m=1,flow_m3_s=1,turbine_efficiency=1,generator_efficiency=1,auxiliary_power_w=0)
        result=run(study)
        self.assertAlmostEqual(result['metrics']['net_electric_power']['value'],9806.65)
        p.update(flow_m3_s=0,auxiliary_power_w=20)
        self.assertEqual(run(study)['metrics']['net_electric_power']['value'],-20)

    def test_tpv_accounting_and_refinement(self):
        study=example('tpv'); first=run(study)
        self.assertLess(abs(first['diagnostics']['energy_balance_residual_w']),1e-10)
        self.assertGreater(first['metrics']['net_electric_power']['value'],0)
        study['solver'].update(geometry_cells=16,spectral_intervals=1024)
        second=run(study)
        p1=first['metrics']['net_electric_power']['value']; p2=second['metrics']['net_electric_power']['value']
        self.assertLess(abs(p1/p2-1),.002)

    def test_dark_tpv_preserves_auxiliary_import(self):
        study=example('tpv'); study['parameters']['emissivity']=0
        result=run(study)
        self.assertEqual(result['metrics']['net_electric_power']['value'],-.1)
        self.assertIsNone(result['metrics']['radiation_to_net_efficiency']['value'])

    def test_rejects_unphysical_diode(self):
        study=example('tpv'); study['parameters']['dark_saturation_current_density_a_m2']=1e-30
        with self.assertRaisesRegex(ValueError,'bandgap'):
            run(study)

    def test_rejects_truncated_spectrum_and_near_field(self):
        study=example('tpv'); study['solver']['wavelength_max_m']=5e-6
        with self.assertRaisesRegex(ValueError,'Spectral window'):
            run(study)
        study=example('tpv'); study['parameters']['gap_m']=1e-6
        with self.assertRaisesRegex(ValueError,'Far-field'):
            run(study)


class EconomicsTests(unittest.TestCase):
    def test_zero_discount_closed_form(self):
        case=example('hydropower')['economics']; case['real_discount_rate']=0
        result=assess(1000,case)
        expected=(50000+20*1500+5000)/(20*4000)
        self.assertAlmostEqual(result['metrics']['lcoe']['value'],expected)

    def test_doubling_output_halves_lcoe(self):
        case=example('hydropower')['economics']
        a=assess(1000,case)['metrics']['lcoe']['value']
        b=assess(2000,case)['metrics']['lcoe']['value']
        self.assertAlmostEqual(a,2*b)

    def test_rejects_nonproducing_case(self):
        for power in (0,-1):
            with self.assertRaises(ValueError):
                assess(power,example('hydropower')['economics'])

    def test_rejects_unlabeled_costs(self):
        case=example('hydropower')['economics']; case['assumption_status']='market_data'
        with self.assertRaises(ValueError):
            assess(1000,case)


class ContractTests(unittest.TestCase):
    def test_catalog_matches_implemented_models(self):
        entries=catalog()['technologies']
        self.assertEqual(len({t['id'] for t in entries}),len(entries))
        self.assertEqual({t['id'] for t in entries if t['engine_runnable']},{'tpv','hydropower'})

    def test_result_is_deterministic_and_snapshot_detached(self):
        study=example('hydropower'); result=run(study)
        self.assertEqual(result,run(copy.deepcopy(study)))
        study['parameters']['head_m']=20
        self.assertEqual(result['input_snapshot']['parameters']['head_m'],10)
        self.assertNotEqual(result['input_sha256'],run(study)['input_sha256'])

    def test_missing_unknown_and_invalid_inputs(self):
        for key,value in [('flow_m3_s',float('nan')),('head_m',True),('turbine_efficiency',1.1),('head_m',-1)]:
            study=example('hydropower'); study['parameters'][key]=value
            with self.assertRaises(ValueError):
                run(study)
        study=example('hydropower'); study['parameters']['unknown']=1
        with self.assertRaises(ValueError):
            run(study)
        study=example('hydropower'); del study['parameters']['flow_m3_s']
        with self.assertRaises(ValueError):
            run(study)

    def test_unsupported_technology(self):
        study=example('hydropower'); study['technology']='nuclear_fusion'
        with self.assertRaisesRegex(ValueError,'Unsupported'):
            run(study)

    def test_cli_reports_and_prevents_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            destination=Path(temp)/'run'
            cmd=[sys.executable,'-m','engine','run',str(ROOT/'systems/hydropower/scenarios/hydropower_reference.json'),'--output',str(destination)]
            output=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(output.returncode,0,output.stderr)
            self.assertTrue((destination/'report.md').is_file())
            data=json.loads((destination/'result.json').read_text())
            self.assertEqual(data['technology'],'hydropower')
            repeated=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(repeated.returncode,2)
            self.assertIn('already exists',repeated.stderr)


if __name__=='__main__':
    unittest.main()
