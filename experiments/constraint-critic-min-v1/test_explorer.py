import csv,json,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import explorer,run_critic
class ExplorerCriticTests(unittest.TestCase):
    def setUp(self):
        self.candidates=explorer.enumerate_candidates()
        self.case=explorer.case_by_id("R01")
        self.signatures={"MTO":"STOPS","MTS":"CONTINUES"}
    def test_enumeration_is_independent_of_case_and_gold(self):
        self.assertEqual({c["id"] for c in self.candidates},{"MTO","MTS"})
        for cid in ("R01","R02","R03","R04"):
            self.assertEqual(len(explorer.enumerate_candidates()),2)
    def test_both_candidates_have_matched_ports(self):
        self.assertTrue(all(c["structurally_valid"] for c in self.candidates))
        self.assertEqual([len(c["links"]) for c in self.candidates],[2,2])
    def test_type_baseline_cannot_disambiguate(self):
        self.assertEqual(explorer.unification_only(self.candidates),["MTO","MTS"])
    def test_omc_signatures_are_read_from_csv_not_hardcoded(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            for name,header,rows in [
              ("mto","time,preparationRate,dispatchRate",["0,0,0","1,0,0"]),
              ("mts","time,production",["0,1","1,1"])]:
                (p/("probe_no_orders_"+name+"_res.csv")).write_text(header+"\n"+"\n".join(rows)+"\n")
            self.assertEqual(explorer.derive_actual_signatures(p),self.signatures)
            (p/"probe_no_orders_mts_res.csv").write_text("time,production\n0,0\n1,0\n")
            with self.assertRaises(ValueError):explorer.derive_actual_signatures(p)
    def review(self,expected,ids=None,question=""):
        return {"case_id":self.case["id"],"test_id":explorer.TEST_ID,
         "expected":expected,"fact_ids":["F1"] if ids is None else ids,
         "next_question":question}
    def test_pruning_is_deterministic_given_reviewed_expectation(self):
        r=self.review("STOPS")
        self.assertEqual(explorer.validate_review(self.case,r)["status"],"VALID_REFERENCE_FORMAT")
        self.assertEqual(explorer.apply_review(self.candidates,self.signatures,r)["kept"],["MTO"])
        r["expected"]="CONTINUES"
        self.assertEqual(explorer.apply_review(self.candidates,self.signatures,r)["kept"],["MTS"])
    def test_unknown_preserves_both(self):
        r=self.review("UNKNOWN",ids=[],question="¿Se fabrica algo cuando no entra ninguna compra?")
        self.assertEqual(explorer.validate_review(self.case,r)["status"],"VALID_REFERENCE_FORMAT")
        self.assertEqual(explorer.apply_review(self.candidates,self.signatures,r)["kept"],["MTO","MTS"])
    def test_conflict_preserves_both(self):
        r=self.review("CONFLICT",ids=["F1","F2"],question="¿Qué documento está vigente?")
        self.assertEqual(explorer.apply_review(self.candidates,self.signatures,r)["kept"],["MTO","MTS"])
    def test_no_unverified_semantic_claim_of_truth(self):
        r=self.review("CONTINUES")
        result=explorer.validate_review(self.case,r)
        self.assertFalse(result["semantic_entailment_verified"])
    def test_reject_nonexistent_fact_or_unregistered_test(self):
        r=self.review("STOPS",ids=["F99"])
        self.assertIn("E_UNKNOWN_FACT",explorer.validate_review(self.case,r)["errors"])
        r=self.review("STOPS");r["test_id"]="FREE_EQUATION"
        self.assertIn("T_UNKNOWN_COUNTERFACTUAL",explorer.validate_review(self.case,r)["errors"])
    def test_prompt_hides_reference_gold_and_numeric_scenario(self):
        text=json.dumps(run_critic.messages(self.case,self.candidates,self.signatures))
        self.assertNotIn("gold.json",text)
        self.assertNotIn("capacityPreparing=",text)
        self.assertNotIn("der(",text)
        self.assertIn("MTO",text)
        self.assertIn("MTS",text)
    def test_exact_citation_text_not_authored_by_critic(self):
        r=self.review("STOPS")
        self.assertEqual(set(r),{"case_id","test_id","expected","fact_ids","next_question"})
        r["quote"]="fabricated evidence"
        self.assertEqual(explorer.validate_review(self.case,r)["status"],"INVALID")
    def test_fenced_json_reader(self):
        r=self.review("STOPS");s=json.dumps(r)
        self.assertEqual(run_critic.parse(s),r)
        mark=chr(96)*3
        self.assertEqual(run_critic.parse(mark+"json\n"+s+"\n"+mark),r)
        with self.assertRaises(ValueError):run_critic.parse(mark+"json\n"+s+"\n"+mark+"\nfoo")
if __name__=="__main__":unittest.main()
