"""Safe-to-publish tests: checks packets and engine without knowing oracle."""
import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from simulator import Config,simulate,ACTIONS,DAYS
from generate import sha

class TestPublic(unittest.TestCase):
    def test_engine_is_deterministic_on_example_seed(self):
        a=simulate(Config(seed=4455),'open_full')
        b=simulate(Config(seed=4455),'open_full')
        self.assertEqual(a['rows'],b['rows'])
        self.assertEqual(a['metrics'],b['metrics'])
    def test_example_accounting_for_each_decision(self):
        for action in ACTIONS:
            run=simulate(Config(seed=4455),action)
            m=run['metrics']
            self.assertEqual(m['attempted'],m['fulfilled_instore']+m['fulfilled_delivery']+
                             m['declined']+m['cancellations']+m['unfinished'])
            self.assertEqual(m['inventory_end']+m['stock_used'],92+m['acquisitions'])
            self.assertEqual(len(run['rows']),DAYS*3)
    def test_public_packet_hashes_and_no_latent_labels(self):
        idx=ROOT/'public/index.json'
        if not idx.exists():self.skipTest('No exported packets mounted')
        index=json.loads(idx.read_text())
        self.assertEqual(len(index['cases']),8)
        forbidden={'gate_role','peak_mult','payout_days','oracle','injection','decision_if_identified'}
        for case in index['cases']:
            p=json.loads((ROOT/'public'/case['case_id']/'packet.json').read_text())
            self.assertEqual(len(p['evidence']['pos_by_arrival_cohort']),42)
            self.assertEqual(len(p['evidence']['daily_stock_finance_snapshots']),14)
            self.assertEqual(p['packet_sha256'],sha({k:v for k,v in p.items() if k!='packet_sha256'}))
            for rows in p['evidence'].values():
                for item in rows:
                    self.assertEqual(item['sha256'],sha({k:item[k] for k in ('source_id','values','units','evidence_type')}))
                    self.assertEqual(set(item['values']),set(item['units']))
            def scan(v):
                if isinstance(v,dict):
                    for k,z in v.items():self.assertNotIn(k,forbidden);scan(z)
                elif isinstance(v,list):
                    for z in v:scan(z)
            scan(p)
    def test_transport_does_not_include_outside_hours_after_cutoff(self):
        from simulator import OPEN,DAY
        r=simulate(Config(seed=4455),'open_full')
        cutoff=(DAYS-1)*DAY+OPEN+360
        self.assertTrue(all(e['t']<=cutoff for e in r['internal_events']))

if __name__=='__main__':unittest.main()
