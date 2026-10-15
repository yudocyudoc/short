"""Offline, zero-cost checks of the source-frozen independent baseline."""
import json,math,unittest
from pathlib import Path
from independent_euler import baseline,lookup

SPEC=json.loads(Path(__file__).with_name("specifications_extracted.json").read_text())

class TestMolecules(unittest.TestCase):
    def test_source_hashes(self):
        self.assertEqual(set(SPEC["models"]),set(SPEC["model_provenance"]))
        self.assertEqual(len(SPEC["models"]),4)
        self.assertTrue(all(len(m["source_sha256"])==64 for m in SPEC["model_provenance"].values()))
    def test_original_timesteps(self):
        self.assertEqual([SPEC["models"][n]["dt"] for n in
            ("delay.mdl","CapUtil.mdl","invbakf.mdl","invbakl.mdl")],[.125,.0625,.125,.125])
    def test_lookup_tables(self):
        self.assertEqual([len(SPEC["models"][n]["lookup"]) for n in
            ("CapUtil.mdl","invbakf.mdl","invbakl.mdl")],[9,10,8])
    def test_capacity_over_nominal(self):
        s=SPEC["models"]["CapUtil.mdl"]
        self.assertAlmostEqual(lookup(s["lookup"],1.4),1.15)
    def test_delay_baseline(self):
        a=baseline("delay.mdl",SPEC["models"]["delay.mdl"])
        self.assertEqual(len(a),41)
        self.assertTrue(all(x["material"]==200 and x["outflow"]==100 for x in a))
    def test_backlog_flow_equilibrium(self):
        a=baseline("invbakf.mdl",SPEC["models"]["invbakf.mdl"])
        self.assertEqual(len(a),49)
        self.assertTrue(all(x["inventory"]==1000 and x["backlog"]==2000 and x["shipping"]==1000 for x in a))
    def test_backlog_level_different(self):
        a=baseline("invbakl.mdl",SPEC["models"]["invbakl.mdl"])
        self.assertEqual(len(a),721)
        self.assertTrue(math.isclose(a[-1]["backlog"],8200.782365102772,rel_tol=1e-10))
    def test_capacity_baseline(self):
        a=baseline("CapUtil.mdl",SPEC["models"]["CapUtil.mdl"])
        self.assertTrue(all(x["production"]==500000 for x in a))

if __name__=="__main__":unittest.main()
