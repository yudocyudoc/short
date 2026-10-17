import importlib.util,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location("dual_construct",HERE/"construct.py")
construct=importlib.util.module_from_spec(spec);spec.loader.exec_module(construct)
import analyze,critic
class DualMoleculeTests(unittest.TestCase):
    def setUp(self):
        self.graphs=construct.enumerate_graphs()
        self.cases=json.loads((HERE/"cases.json").read_text())["cases"]
        self.sig={
          "OBSERVED_VS_DISPATCH":{"Direct":"SYNC","ReportOnly":"LAG","TransitOnly":"LAG","TransitAndReport":"LAG"},
          "PHYSICAL_VS_DISPATCH":{"Direct":"SYNC","ReportOnly":"SYNC","TransitOnly":"LAG","TransitAndReport":"LAG"},
          "OBSERVED_VS_PHYSICAL":{"Direct":"SYNC","ReportOnly":"LAG","TransitOnly":"SYNC","TransitAndReport":"LAG"}
        }
    def test_all_four_graphs_generated_from_two_optionals(self):
        self.assertEqual(len(self.graphs),4)
        self.assertEqual({g["id"] for g in self.graphs},set(construct.ALIASES.values()))
        self.assertEqual(sorted(len(g["optionals"]) for g in self.graphs),[0,1,1,2])
    def test_molecule_types_for_material_and_informational_branches(self):
        for g in self.graphs:
            self.assertTrue(g["type_checked"])
            self.assertTrue(all(e["type"].startswith(("FLOW<","SIGNAL<")) for e in g["edges"]))
            self.assertTrue(any(e["to"]=="OBSERVED.in" for e in g["edges"]))
        self.assertEqual(construct.PORTS["TRANSIT"]["in"],("FLOW","Shipment"))
        self.assertEqual(construct.PORTS["REPORT_FILTER"]["in"],("SIGNAL","DeliveryRate"))
        self.assertNotEqual(construct.PORTS["TRANSIT"]["in"],construct.PORTS["REPORT_FILTER"]["in"])
    def test_native_modelica_has_distinct_mechanisms_and_real_connectors(self):
        src=construct.compile_graphs(self.graphs)
        for name in construct.ALIASES.values():
            self.assertIn("model "+name,src)
        self.assertIn("IGCMolecules.BoundedQueue transit",src)
        self.assertIn("IGCInformationMolecules.FirstOrderReportFilter reporter",src)
        self.assertIn("connect(dispatch.completed,transit.arrival)",src)
        self.assertIn("connect(transit.completed,delivered.arrival)",src)
        self.assertIn("connect(dispatch.completed,delivered.arrival)",src)
        self.assertIn("reportedDeliveryRate = reporter.reportedRate;",src)
        self.assertNotIn("der(",src)
    def test_incompatible_material_to_information_edge_fails(self):
        with self.assertRaises(ValueError):
            construct.verify_link("DISPATCH.out","REPORT_FILTER.in")
    def test_zero_orders_is_nondiscriminating_and_observed_lag_keeps_three(self):
        self.assertEqual(len({self.sig["OBSERVED_VS_DISPATCH"][n] for n in self.sig["OBSERVED_VS_DISPATCH"] if n!="Direct"}),1)
        self.assertEqual(len([n for n,v in self.sig["OBSERVED_VS_DISPATCH"].items() if v=="LAG"]),3)
    def test_remaining_three_have_a_useful_second_test(self):
        remaining=["ReportOnly","TransitOnly","TransitAndReport"]
        test=analyze.next_experiment(self.sig,remaining,("OBSERVED_VS_DISPATCH",))
        self.assertIn(test,("PHYSICAL_VS_DISPATCH","OBSERVED_VS_PHYSICAL"))
        self.assertEqual(len(set(self.sig[test][x] for x in remaining)),2)
    def test_joint_signatures_separate_all_four(self):
        self.assertEqual(len({tuple(self.sig[t][n] for t in analyze.TESTS) for n in self.sig["OBSERVED_VS_DISPATCH"]}),4)
    def review(self,cid,vector):
        return {"case_id":cid,"tests":dict(zip(analyze.TESTS,vector)),
          "fact_ids":{t:(["F1","F2"] if v=="CONFLICT" else ["F1"] if v in ("SYNC","LAG") else []) for t,v in zip(analyze.TESTS,vector)},
          "next_question":"¿Podemos medir independientemente la recepción y el indicador publicado?" if any(x in ("UNKNOWN","CONFLICT") for x in vector) else ""}
    def test_known_evidence_picks_exact_combo(self):
        r=self.review("D02",("LAG","SYNC","LAG"))
        self.assertEqual(critic.validate(self.cases[1],r)["status"],"VALID_FORMAT")
        self.assertEqual(critic.apply(r,self.sig)["survivors_conditional_on_critic_premises"],["ReportOnly"])
    def test_only_observed_lag_still_keeps_three(self):
        r=self.review("D05",("LAG","UNKNOWN","UNKNOWN"))
        self.assertEqual(critic.validate(self.cases[4],r)["status"],"VALID_FORMAT")
        out=critic.apply(r,self.sig)
        self.assertEqual(len(out["survivors_conditional_on_critic_premises"]),3)
        self.assertIsNotNone(out["next_measurement_to_collect_if_observable"])
    def test_physical_transport_with_unknown_reporting_keeps_two(self):
        r=self.review("D06",("UNKNOWN","LAG","UNKNOWN"))
        self.assertEqual(len(critic.apply(r,self.sig)["survivors_conditional_on_critic_premises"]),2)
    def test_conflict_blocks_irreversible_pruning(self):
        r=self.review("D07",("UNKNOWN","CONFLICT","UNKNOWN"))
        self.assertEqual(critic.validate(self.cases[6],r)["status"],"VALID_FORMAT")
        self.assertEqual(len(critic.apply(r,self.sig)["survivors_conditional_on_critic_premises"]),4)
    def test_critic_cannot_invent_id_or_unregistered_test(self):
        r=self.review("D01",("LAG","LAG","SYNC"))
        r["fact_ids"]["OBSERVED_VS_PHYSICAL"]=["F99"]
        self.assertEqual(critic.validate(self.cases[0],r)["status"],"INVALID")
        r=self.review("D01",("LAG","LAG","SYNC"))
        r["tests"]["FAKE_TEST"]="SYNC"
        self.assertEqual(critic.validate(self.cases[0],r)["status"],"INVALID")
    def test_no_gold_equations_or_numeric_model_parameters_sent_to_llm(self):
        msgs=json.dumps(critic.messages(self.cases[0],self.sig),ensure_ascii=False)
        self.assertNotIn("gold.json",msgs)
        self.assertNotIn("reportResponseTime=0.8",msgs)
        self.assertNotIn("der(",msgs)
        self.assertIn("TransitAndReport",msgs)
    def test_parser_supports_one_json_fence_not_arbitrary_repair(self):
        q=json.dumps(self.review("D01",("LAG","LAG","SYNC")))
        fence=chr(96)*3
        self.assertEqual(critic.parse(fence+"json\n"+q+"\n"+fence),json.loads(q))
        with self.assertRaises(ValueError):critic.parse(fence+"json\n"+q+"\n"+fence+"\nEXTRA")
    def test_frozen_gold_has_eight_cases_and_three_dimensions(self):
        x=json.loads((HERE/"gold.json").read_text())
        self.assertEqual(len(x["labels"]),8)
        self.assertTrue(all(set(v)==set(analyze.TESTS) for v in x["labels"].values()))
if __name__=="__main__":unittest.main()
