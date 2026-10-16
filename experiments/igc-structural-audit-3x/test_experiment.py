import json, unittest
from pathlib import Path
from probes import interp, stock_run, fluid_proxy, report, check_ledger_mutations
from runner import prompt
ROOT=Path(__file__).resolve().parent
C={c['case_id']:c for c in json.loads((ROOT/'cases.json').read_text(encoding='utf-8'))['cases']}

class TestIndependentProbes(unittest.TestCase):
    def test_bb_series_and_lookup(self):
        a=C['BB01']['observed_sales_by_quarter_hour']
        self.assertEqual([sum(a[d]) for d in ['2017-02-04','2016-10-30']],[139,79])
        self.assertTrue(all(len(a[d])==96 for d in a))
        self.assertAlmostEqual(interp(C['BB01']['equations_and_design']['lookup_points'],0.164706),0.234875)
    def test_bb_six_production_integrals(self):
        for p in report(C['BB01'])['arithmetic_probes']['scenario_probes']:
            src=next(r for r in C['BB01']['simulated_outputs'] if r['date']==p['day'] and r['capacity']==p['capacity'])
            self.assertAlmostEqual(p['production_from_lookup_integral'],src['produced'],places=5)
    def test_bb_fluid_independent(self):
        probes=report(C['BB01'])['arithmetic_probes']['scenario_probes']
        target={(p['day'],p['capacity']):p['fluid_proxy']['end_of_24h'] for p in probes}
        self.assertEqual(target[('2017-02-04',8)],18)
        self.assertEqual(target[('2016-10-30',8)],0)
    def test_control_trajectory_matched_source(self):
        for case in [C['W17'],C['W18']]:
            rows=stock_run(case)
            self.assertEqual([r['inventory_end'] for r in rows],case['simulated_inventory_end_by_day'])
            self.assertEqual([r['shipped_units'] for r in rows],case['simulated_shipments_by_day'])
            self.assertEqual(sum(r['received_units'] for r in rows),12)
            self.assertEqual(sum(r['shipped_units'] for r in rows),21)
        self.assertEqual(stock_run(C['W17'])[1]['received_units'],12)
        self.assertEqual(stock_run(C['W18'])[3]['received_units'],12)
    def test_conservation_mutants_are_not_domain_tests(self):
        mutants=check_ledger_mutations()
        self.assertEqual(len(mutants),3)
        self.assertTrue(all(abs(m['backlog_conservation_residual'])<1e-9 and abs(m['inventory_conservation_residual'])<1e-9 for m in mutants))
        self.assertLess(mutants[2]['prepared_stock_end'],0)
    def test_no_tools_given_to_A(self):
        for c in C.values():
            a=prompt(c,'A');b=prompt(c,'B')
            self.assertNotIn('RESULTADOS DE HERRAMIENTAS',a)
            self.assertIn('RESULTADOS DE HERRAMIENTAS',b)
            self.assertTrue(b.startswith(a))
    def test_no_labels_in_candidate_prompts(self):
        for c in C.values():
            for arm in ['A','B']:
                p=prompt(c,arm)
                self.assertNotIn('W17 tiene error',p)
                self.assertNotIn('W18 es correcto',p)
                self.assertNotIn('Sobreproducción es propiedad',p)

if __name__=='__main__':unittest.main()
