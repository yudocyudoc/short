import csv,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location("graph_enumerator",HERE/"enumerate.py")
enum=importlib.util.module_from_spec(spec)
spec.loader.exec_module(enum)
import analyze_probes,review

class ComposeAndCriticTests(unittest.TestCase):
    def setUp(self):
        self.graphs=enum.enumerate_graphs()
        self.cases=json.loads((HERE/"cases.json").read_text())["cases"]
        self.second={"status":"PASS",
            "signatures":{"NO_ACCEPTED_ORDERS":{"Direct":"STOPS","Buffered":"STOPS"},
                          "DISPATCH_TO_DELIVERY_LAG":{"Direct":"SYNC","Buffered":"LAG"}},
            "best_discriminating_test":"DISPATCH_TO_DELIVERY_LAG"}
    def test_optional_molecule_creates_two_different_graphs(self):
        self.assertEqual({x["id"] for x in self.graphs},{"Direct","Buffered"})
        self.assertEqual(sorted(len(g["nodes"]) for g in self.graphs),[4,5])
        self.assertTrue(enum.checked(self.graphs))
    def test_all_edges_typed_from_catalog_not_mandatory_fixed_link_list(self):
        for graph in self.graphs:
            self.assertTrue(all("type" in e and e["type"].startswith("FLOW<") for e in graph["links"]))
            self.assertEqual(len(graph["links"]),len(graph["nodes"])-1)
    def test_generated_modelica_contains_real_extra_molecule_and_connection(self):
        source=enum.render(self.graphs)
        self.assertIn("model Direct",source)
        self.assertIn("model Buffered",source)
        self.assertIn("IGCMolecules.BoundedQueue transit",source)
        self.assertIn("connect(dispatch.completed,transit.arrival)",source)
        self.assertIn("connect(transit.completed,delivered.arrival)",source)
        self.assertIn("connect(dispatch.completed,delivered.arrival)",source)
        self.assertNotIn("der(",source)
        self.assertNotIn("outside_data",source)
    def test_unregistered_component_is_not_accepted(self):
        g=json.loads(json.dumps(self.graphs[0]))
        g["nodes"].append("FLYING_TRANSPORT")
        with self.assertRaises(ValueError):enum.emit_model(g)
    def test_first_probe_nondiscriminating_second_discriminating(self):
        self.assertEqual(len(set(self.second["signatures"]["NO_ACCEPTED_ORDERS"].values())),1)
        self.assertEqual(len(set(self.second["signatures"]["DISPATCH_TO_DELIVERY_LAG"].values())),2)
    def test_measured_signatures_come_from_series_and_wrong_data_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            fields=["acceptedRate","preparationRate","dispatchRate","deliveryRate","inTransit","deliveredOrders","unpreparedOrders","preparedOrders"]
            def write(name,buffered=False,zero=False):
                with (p/(name+"_res.csv")).open("w",newline="") as h:
                    w=csv.DictWriter(h,fieldnames=["time"]+fields)
                    w.writeheader()
                    for i in range(9):
                        dispatch=0 if zero else i/10
                        delivery=dispatch/2 if buffered and not zero else dispatch
                        transit=0 if zero or not buffered else i/3
                        w.writerow({"time":i,**{k:(0 if zero else 1) for k in fields},
                          "dispatchRate":dispatch,"deliveryRate":delivery,"inTransit":transit,
                          "unpreparedOrders":0,"preparedOrders":0,"deliveredOrders":0})
            write("no_orders_direct",zero=True)
            write("no_orders_buffered",zero=True)
            write("pulse_direct")
            write("pulse_buffered",buffered=True)
            res=analyze_probes.inspect(p)
            self.assertEqual(res["signatures"]["DISPATCH_TO_DELIVERY_LAG"],{"Direct":"SYNC","Buffered":"LAG"})
            self.assertEqual(res["best_discriminating_test"],"DISPATCH_TO_DELIVERY_LAG")
            write("pulse_buffered",buffered=False)
            with self.assertRaisesRegex(ValueError,"TRANSIT_BUFFER_NOT_BEHAVIORALLY_DISTINCT"):
                analyze_probes.inspect(p)
    def test_review_can_select_buffered_or_direct_but_not_both(self):
        for expected,chosen in [("SYNC",["Direct"]),("LAG",["Buffered"])]:
            result=review.filter_models({"expected":expected},self.second)
            self.assertEqual(result["second_test_survivors_conditional_on_llm_premise"],chosen)
            self.assertEqual(len(result["first_test_survivors"]),2)
    def test_unknown_and_conflict_keep_both(self):
        for state in ("UNKNOWN","CONFLICT"):
            self.assertEqual(len(review.filter_models({"expected":state},self.second)["second_test_survivors_conditional_on_llm_premise"]),2)
    def test_linter_does_not_prove_semantic_truth(self):
        r={"case_id":"C01","test_id":review.TEST,"expected":"SYNC","fact_ids":["F1"],"next_question":""}
        verdict=review.validate(self.cases[0],r)
        self.assertEqual(verdict["status"],"VALID_FORMAT")
        self.assertIs(verdict["semantic_entailment_verified"],False)
    def test_linter_rejects_fake_reference_and_test(self):
        r={"case_id":"C01","test_id":review.TEST,"expected":"LAG","fact_ids":["F9"],"next_question":""}
        self.assertEqual(review.validate(self.cases[0],r)["status"],"INVALID")
        r["fact_ids"]=["F1"];r["test_id"]="FAKE_TEST"
        self.assertEqual(review.validate(self.cases[0],r)["status"],"INVALID")
    def test_no_modelica_equations_or_scenario_numbers_in_critic_prompt(self):
        msg=json.dumps(review.messages(self.cases[0],self.second))
        self.assertIn("Buffered",msg)
        self.assertIn("Direct",msg)
        self.assertNotIn("transitResponseTime=1.5",msg)
        self.assertNotIn("der(",msg)
        self.assertNotIn("gold.json",msg)
    def test_unknown_requires_discriminating_question(self):
        r={"case_id":"C03","test_id":review.TEST,"expected":"UNKNOWN","fact_ids":["F1"],"next_question":""}
        self.assertEqual(review.validate(self.cases[2],r)["status"],"INVALID")
        r["next_question"]="¿Cuándo llega realmente el producto al destinatario?"
        self.assertEqual(review.validate(self.cases[2],r)["status"],"VALID_FORMAT")
    def test_fenced_json(self):
        raw=json.dumps({"a":1})
        self.assertEqual(review.parse(raw),{"a":1})
        mark=chr(96)*3
        self.assertEqual(review.parse(mark+"json\n"+raw+"\n"+mark),{"a":1})
        with self.assertRaises(ValueError):review.parse(mark+"json\n"+raw+"\n"+mark+"\nextra")
if __name__=="__main__":unittest.main()
