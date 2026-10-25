"""E0 checks include negative controls. Passing tests do not claim S1/S2."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("e0_contract", HERE / "check_contract.py")
e0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e0)
CATALOG, PROTOCOL = e0.load_contracts()


def graph(n_transit=0, has_report=False):
    if n_transit not in (0, 1, 2):
        raise ValueError("fixture only, not a composer")
    xs = [
        {"id":"source","class_id":"accepted-source","role":"source","parameters":{}},
        {"id":"prep","class_id":"bounded-queue","role":"preparation","parameters":{"maxThroughput":20,"responseTime":0.5}},
        {"id":"dispatch","class_id":"bounded-queue","role":"dispatch","parameters":{"maxThroughput":20,"responseTime":0.5}},
        {"id":"receipt","class_id":"delivery-counter","role":"receipt","parameters":{}}
    ]
    edges = [
        {"from":"source.outflow","to":"prep.arrival","adapter":None},
        {"from":"prep.completed","to":"dispatch.arrival","adapter":None}
    ]
    last="dispatch"
    for i in range(n_transit):
        name="transit" + str(i)
        xs.append({"id":name,"class_id":"bounded-queue","role":"transit","parameters":{"maxThroughput":3,"responseTime":1.6/n_transit}})
        edges.append({"from":last+".completed","to":name+".arrival","adapter":None})
        last=name
    edges.append({"from":last+".completed","to":"receipt.arrival","adapter":None})
    if has_report:
        xs.append({"id":"report","class_id":"first-order-report-filter","role":"report","parameters":{"reportResponseTime":1.6}})
        edges.append({"from":last+".completed","to":"report.physicalArrivalRate","adapter":"receipt-rate-tap"})
    return {"instances":xs,"links":edges}


class E0ContractTests(unittest.TestCase):
    def test_contract_and_original_sources(self):
        self.assertEqual(e0.validate_contracts(CATALOG,PROTOCOL),[])

    def test_six_manual_graphs_expressible_without_generator(self):
        signatures=set()
        for n in (0,1,2):
            for report in (False,True):
                g=graph(n,report)
                self.assertEqual(e0.validate_graph(g,CATALOG),[],(n,report))
                signatures.add(e0.canonical(g))
        self.assertEqual(len(signatures),6)

    def test_renamed_instances_share_topological_canonical_hash(self):
        g=graph(2,True)
        r=copy.deepcopy(g)
        mapping={x["id"]:"node"+str(i) for i,x in enumerate(r["instances"])}
        for x in r["instances"]:
            x["id"]=mapping[x["id"]]
        for edge in r["links"]:
            for field in ("from","to"):
                node,port=edge[field].split(".")
                edge[field]=mapping[node]+"."+port
        self.assertEqual(e0.validate_graph(r,CATALOG),[])
        self.assertEqual(e0.canonical(g),e0.canonical(r))

    def test_wrong_material_vs_signal_rejected(self):
        g=graph(0,True)
        g["links"][-1]["adapter"]=None
        self.assertIn("TYPE_MISMATCH",e0.validate_graph(g,CATALOG))

    def test_misplaced_observation_rejected(self):
        g=graph(1,True)
        g["links"][-1]["from"]="dispatch.completed"
        self.assertIn("REPORT_NOT_TAPPED_AT_RECEIPT",e0.validate_graph(g,CATALOG))

    def test_disallow_third_transit(self):
        g=graph(2,True)
        g["instances"].append({"id":"transit2","class_id":"bounded-queue","role":"transit","parameters":{"maxThroughput":3,"responseTime":0.8}})
        self.assertIn("ROLE_LIMIT:transit",e0.validate_graph(g,CATALOG))

    def test_out_of_bounds_parameter(self):
        g=graph(1)
        g["instances"][-1]["parameters"]["responseTime"]=-1
        self.assertIn("PARAMETER_OUT_OF_BOUNDS",e0.validate_graph(g,CATALOG))

    def test_no_duplicate_or_unconnected(self):
        g=graph(0)
        g["links"].pop()
        self.assertTrue(any(x.startswith("MATERIAL_IN_DEGREE") for x in e0.validate_graph(g,CATALOG)))
        g=graph(1)
        g["links"].append(copy.deepcopy(g["links"][0]))
        self.assertIn("DUPLICATE_LINK",e0.validate_graph(g,CATALOG))

    def test_rejects_disconnected_typed_material_cycle(self):
        g=graph(2)
        # Source→prep→dispatch→receipt looks fine, but transits form a closed
        # disconnected cycle. Every port has legal types and degrees.
        g["links"][-3]["to"]="receipt.arrival"  # dispatch → receipt
        g["links"][-1]["to"]="transit0.arrival"  # transit1 → transit0
        self.assertIn("PHYSICAL_PATH_NOT_CONNECTED",e0.validate_graph(g,CATALOG))

    def test_gold_not_revealed_in_description(self):
        p=copy.deepcopy(PROTOCOL)
        p["neutral_description"]="Hay dos colas y un filtro."
        self.assertTrue(any(x.startswith("FUNCTIONAL_TEXT_LEAK") for x in e0.validate_contracts(CATALOG,p,False)))

    def test_oracle_budget_not_unlimited(self):
        p=copy.deepcopy(PROTOCOL)
        p["budgets"]["world_responses_total"]=100
        self.assertIn("ORACLE_BUDGET_NOT_BALANCED",e0.validate_contracts(CATALOG,p,False))

    def test_wrong_profile_exposes_gold(self):
        p=copy.deepcopy(PROTOCOL)
        p["observation_profiles"]["Q"]["visible"].append("trueGraph")
        self.assertIn("GOLD_VISIBLE",e0.validate_contracts(CATALOG,p,False))


if __name__=="__main__":
    unittest.main()
