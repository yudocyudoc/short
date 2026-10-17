import json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from evaluate import CASES,GOLD,MOLECULES,assess,summarize,clean_response
from deterministic import respond
from run_llm import messages,ARMS

class Pilot(unittest.TestCase):
 def test_case_set_and_gold_match(self):
  self.assertEqual(len(CASES),12)
  self.assertEqual(set(GOLD),set(CASES))
  self.assertTrue(any(not g['molecules'] for g in GOLD.values()))
  self.assertTrue(any(len(g['molecules'])>1 for g in GOLD.values()))
  for c,g in GOLD.items():
   self.assertTrue(set(g['molecules']).issubset(MOLECULES))
   self.assertEqual(set(g['supported_facts']),set(g['molecules']))
   ids={f['id'] for f in CASES[c]['facts']}
   for refs in g['supported_facts'].values():self.assertTrue(set(refs).issubset(ids))
 def test_no_numerical_case_data(self):
  for case in CASES.values():
   for f in case['facts']:
    self.assertFalse(any(ch.isdigit() for ch in f['text']))
 def test_prepared_prompts_do_not_leak_gold_or_score(self):
  for case in CASES.values():
   for arm in ARMS:
    msg=json.dumps(messages(case,arm),ensure_ascii=False)
    for forbidden in ('gold_private.json','supported_facts','selection_exact','P01": {"molecules"'):
     self.assertNotIn(forbidden,msg)
 def test_same_facts_both_arms_different_scaffold(self):
  for c in CASES.values():
   a=messages(c,ARMS[0]);b=messages(c,ARMS[1])
   self.assertEqual(json.loads(a[1]['content'])['facts'],json.loads(b[1]['content'])['facts'])
   self.assertNotIn('molecular_contracts',json.loads(a[1]['content']))
   self.assertIn('molecular_contracts',json.loads(b[1]['content']))
 def test_rules_baseline_does_not_import_key(self):
  self.assertNotIn('gold_private', (HERE/'deterministic.py').read_text())
  self.assertNotIn('GOLD', (HERE/'deterministic.py').read_text())
  for case in CASES.values():
   r=respond(case)
   self.assertIsInstance(r['molecules'],list)
   self.assertTrue(assess(case['id'],r)['parsed'])
 def test_literal_quote_not_semantic_support(self):
  c=CASES['P01']
  p={'decision':'COMPOSE','molecules':['CAP_UTIL'],
     'citations':[{'target':'CAP_UTIL','fact_id':'F1','quote':c['facts'][0]['text']}],
     'unresolved':[]}
  x=assess('P01',p)
  self.assertTrue(x['literal_quotes_valid'])
  self.assertFalse(x['supported_citations'])
 def test_quote_fabrication_is_rejected(self):
  p=respond(CASES['P02']);p['citations'][0]['quote']='THIS DID NOT APPEAR IN THE SOURCE'
  self.assertFalse(assess('P02',p)['literal_quotes_valid'])
 def test_syntax_extra_fields_rejected(self):
  p=respond(CASES['P02']);p['equation']='der(x)=42'
  self.assertFalse(assess('P02',p)['parsed'])
 def test_missing_real_inferences_cannot_pass(self):
  s=summarize({},'generic_sd')
  self.assertEqual(s['evaluated'],0)
  self.assertEqual(s['strict_pass'],0)
 def test_quote_in_wrong_fact_rejected(self):
  p=respond(CASES['P01']);p['citations'][0]['fact_id']='F99'
  self.assertFalse(assess('P01',p)['literal_quotes_valid'])

if __name__=='__main__':unittest.main()
