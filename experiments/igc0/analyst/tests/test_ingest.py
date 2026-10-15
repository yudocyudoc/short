import copy,json,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'src'))
from prepare import read_public,summarize,sha,check_record
from igc import reference_graph,validate_model,diagram
from aggregate_sd import simulate
ZIP=P/'inputs'/'IGC0_8_mundos_analista.zip'

class TestIGC(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cases=read_public(ZIP)
  cls.packets={k:summarize(p) for k,p in cls.cases.items()}
 def test_all_public_hashes_and_lengths(self):
  self.assertEqual(len(self.cases),8)
  self.assertEqual(sum(len(x['pos_by_arrival_cohort']) for x in self.packets.values()),336)
  self.assertEqual(sum(len(x['daily_stocks']) for x in self.packets.values()),112)
 def test_tampered_source_is_rejected(self):
  x=copy.deepcopy(self.cases['M01']['evidence']['pos_by_arrival_cohort'][0]);x['values']['presencial_attempted']+=1
  with self.assertRaises(ValueError):check_record(x)
 def test_scaffold_keeps_pipes_and_stocks_separate(self):
  for p in self.packets.values():
   g=reference_graph(p);d=diagram(g)
   self.assertTrue(validate_model(g,p)['accepted'])
   self.assertIn('flowchart LR',d)
   self.assertEqual(g['scenario_projections'],[])
   self.assertEqual(g['decision']['choice'],'abstain')
 def test_bad_evidence_reference_rejected(self):
  p=self.packets['M01'];g=reference_graph(p)
  g['pipes'][0]['evidence_refs'][0]['sha256']='0'*64
  r=validate_model(g,p)
  self.assertFalse(r['accepted'])
  self.assertTrue(any(x['code']=='UNVERIFIED_SOURCE' for x in r['issues']))
 def test_no_numeric_forecast_without_run(self):
  p=self.packets['M01'];g=reference_graph(p)
  g['scenario_projections']=[{'decision':'no_delivery','metrics':[{'id':'cash','value':1,'unit':'MXN','label':'SIMULADO'}]}]
  self.assertFalse(validate_model(g,p)['accepted'])
 def test_arrival_vs_execution_not_interchangeable(self):
  p=self.packets['M02'];r=p['horizon_totals']
  self.assertIn('delivery_fulfilled',r);self.assertIn('delivery_service_window_completed',r)
 def test_aggregate_sim_is_independent_and_provenance_labeled(self):
  p=self.packets['M01']
  a=simulate(p,'open_full');b=simulate(p,'open_full')
  self.assertEqual(a,b)
  self.assertEqual(a['engine'],'IGC0_AGGREGATED_REFERENCE_V0_NOT_CALIBRATED')
  self.assertEqual(len(a['windows']),42)
  self.assertGreaterEqual(a['final_inventory'],0)
 def test_ingredient_purchase_not_counted_twice_in_cash(self):
  import copy
  p=copy.deepcopy(self.packets['M01'])
  # Create a cash experiment with a single sale and no supplier restocking.
  for r in p['pos_by_arrival_cohort']:
   r['presencial_attempted']=0;r['delivery_attempted']=0
  p['pos_by_arrival_cohort'][0]['presencial_attempted']=1
  p['operating_reference']['initial_conditions']['inventory_meals']['value']=10000
  p['operating_reference']['initial_conditions']['supplier_reorder_threshold_meals']['value']=0
  a=simulate(p,'no_delivery')
  initial_cash=p['operating_reference']['initial_conditions']['cash_mxn']['value']
  fixed=p['operating_reference']['initial_conditions']['fixed_daily_cost_mxn']['value']
  self.assertEqual(a['final_cash'],initial_cash-14*fixed+120)
  # Already-paid inventory is not a second cash expense when a meal is prepared.
  p['operating_reference']['reference']['meal_input_cost_mxn']['value']=900
  b=simulate(p,'no_delivery')
  self.assertEqual(a['final_cash'],b['final_cash'])
 def test_invalid_policy_refused(self):
  with self.assertRaises(AssertionError):simulate(self.packets['M01'],'open_all_magic')

if __name__=='__main__':unittest.main()
