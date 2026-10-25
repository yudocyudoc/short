import importlib.util,json,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("epi_build",HERE/"build_contexts.py")
builder=importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
run_spec=importlib.util.spec_from_file_location("epi_runner",HERE/"scripts/run_cloudflare.py")
runner=importlib.util.module_from_spec(run_spec); run_spec.loader.exec_module(runner)
CASE=json.loads((HERE/"case.json").read_text(encoding="utf-8"))

class Epi01DesignTests(unittest.TestCase):
    def test_pinned_igc_atms_probe_matches_or_and_for_fixture(self):
        logical=builder.build(CASE)["C"]["logical_context"]
        self.assertEqual(logical["engine_equivalence"]["result"],"EXACT_FOR_EPI01_FIXTURE")
        self.assertEqual(logical["engine_equivalence"]["reference"],"IGC_F0_AtmsProbe")
        self.assertEqual(logical["before_review_minimal_support_environments"]["CS-02"],
          [["A-CS02-structure","A-layout-current"],["A-CS02-structure","A-transfer-reliable"]])
        self.assertEqual(logical["current_minimal_support_environments"]["CS-02"],
          [["A-CS02-structure","A-layout-current"]])
    def test_all_arms_share_evidence_and_original_justifications(self):
        arms=builder.build(CASE)
        for arm in arms.values():
            for key in ("records","claims","hypotheses","assumptions","justifications","revisions","tasks"):
                self.assertEqual(arm[key],arms["A"][key])
        self.assertNotIn("current_hypothesis_status",arms["A"])
        self.assertIn("current_hypothesis_status",arms["B"])
        self.assertNotIn("logical_context",arms["B"])
        self.assertIn("logical_context",arms["C"])
    def test_context_does_not_give_t3_candidate_observation_or_evaluation_reference(self):
        with tempfile.TemporaryDirectory() as d:
            builder.write_contexts(HERE/"case.json",Path(d))
            for f in Path(d).glob("context-*.json"):
                text=f.read_text(encoding="utf-8").lower()
                self.assertNotIn("candidate_observation",text)
                self.assertNotIn("conteos sincronizados",text)
                self.assertNotIn("expected",text)
                self.assertNotIn("rubric",text)
                self.assertNotIn("not_for_model",text)
    def test_preparation_makes_no_calls(self):
        with tempfile.TemporaryDirectory() as d:
            report=builder.write_contexts(HERE/"case.json",Path(d))
            self.assertEqual((report["calls_made"],report["calls_planned"]),(0,9))
            self.assertEqual(report["atms_or_and_equivalence"],"EXACT_FOR_EPI01_FIXTURE")
    def test_inference_requires_explicit_authorization_before_network(self):
        attempted=[]
        def sender(*args,**kwargs):
            attempted.append(True)
            raise AssertionError("network must not be called")
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                runner.run(HERE,Path(d),env={"CLOUDFLARE_ACCOUNT_ID":"x","CLOUDFLARE_API_TOKEN":"y"},request_sender=sender)
        self.assertEqual(attempted,[])
        self.assertEqual(runner.MAX_CALLS,9)
        self.assertEqual(runner.AUTH,"RUN_EPI01_MAX9")
if __name__=="__main__": unittest.main()
