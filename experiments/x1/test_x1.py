"""Controls for X1: falsifiability, rivals, no secret world access and abstention."""
import inspect,json,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import build,evaluator,participants

def toy():
    return {
      "M_A":{"actions":{"none":{"net_units":10},"upgrade_preparation":{"net_units":15},"upgrade_distribution":{"net_units":8}},
              "observables":{"measure_departures":3,"measure_in_route":2,"inspect_dashboard":4}},
      "M_B":{"actions":{"none":{"net_units":10},"upgrade_preparation":{"net_units":8},"upgrade_distribution":{"net_units":15}},
              "observables":{"measure_departures":8,"measure_in_route":5,"inspect_dashboard":4}}
    }

class X1Tests(unittest.TestCase):
    def test_molecular_counterfactuals_are_expressible_in_e1(self):
        cfg,cl,g=build.base_graph()
        self.assertTrue(all(build.updated(g,m,a) for m in build.CANDIDATES for a in build.ACTIONS))
        # Action changes only a bound physical capacity, never equations or AST edges.
        for m in build.CANDIDATES:
            for a in build.ACTIONS:
                v=build.updated(g,m,a)
                self.assertEqual(g["links"],v["links"])
                self.assertEqual(len(g["instances"]),len(v["instances"]))
                self.assertTrue(v["instances"])
    def test_preflight_can_fail_when_both_worlds_favor_same_action(self):
        opts=toy()
        fake={m:opts[m]["actions"] for m in opts}
        best={m:max(build.ACTIONS,key=lambda x:opts[m]["actions"][x]["net_units"]) for m in opts}
        self.assertNotEqual(best["M_A"],best["M_B"])
        for m in opts:
            opts[m]["actions"]["upgrade_distribution"]["net_units"]=30
        best={m:max(build.ACTIONS,key=lambda x:opts[m]["actions"][x]["net_units"]) for m in opts}
        self.assertEqual(best["M_A"],best["M_B"])
    def test_baseline_b_picks_probes_for_decisions_not_for_graph_labels(self):
        x=toy();meta={p:{"cost":0.8} for p in build.PROBES}
        self.assertEqual(participants.choose_probe_B(x,list(build.PROBES),meta),
                         "measure_departures") # deterministic tie by menu order
        self.assertIsNone(participants.choose_probe_B(x,[],meta))
        self.assertEqual(participants.action_for(x,list(x)),"abstain")
        self.assertEqual(participants.action_for(x,["M_A"]),"upgrade_preparation")
    def test_weak_reporter_does_not_falsely_identify_world(self):
        x=toy()
        self.assertEqual(participants.matching(x,"inspect_dashboard",4),list(x))
        self.assertEqual(participants.action_for(x,participants.matching(x,"inspect_dashboard",4)),"abstain")
    def test_cloudflare_provider_response_choices_fallback(self):
        cloudflare={"success":True,"result":{
            "response":None,
            "choices":[{"message":{"content":'{"probe":null,"reason":"no","uncertainty":"unknown"}'}}]
        }}
        self.assertEqual(participants.extract_provider_content(cloudflare),
                         '{"probe":null,"reason":"no","uncertainty":"unknown"}')
        self.assertEqual(participants.extract_provider_content(
            {"success":True,"result":{"response":"TEXT"}}),"TEXT")
        with self.assertRaisesRegex(ValueError,"MISSING_PROVIDER_TEXT"):
            participants.extract_provider_content({"success":True,"result":{"response":None}})

    def test_evaluator_truth_is_not_imported_into_participant(self):
        code=inspect.getsource(participants)
        self.assertNotIn("private_truth.json",code)
        self.assertNotIn("world_by_case",code)
        self.assertNotIn("eval(",code)
        self.assertNotIn("exec(",code)
    def test_specified_budget_and_roles(self):
        self.assertEqual(len(build.PROBES),3)
        self.assertEqual(len(build.CANDIDATES),2)
        self.assertEqual(len(evaluator.CASE_IDS),6)
        self.assertEqual(len(evaluator.NO_PROBE),1)
        self.assertTrue(all(a in build.ACTIONS for a in ("upgrade_preparation","upgrade_distribution")))
if __name__=="__main__":unittest.main()
