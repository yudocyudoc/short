import copy
import unittest
from arena.core import view_for_lane, seal_submission, adjudicate, digest


CASE = {
 "schema_version": "cei.arena.v0.1", "case_id": "CAF-DEMO-001",
 "question": "¿Qué explica menos ventas?", "agent": {
  "controls": ["turnos"], "influences": ["reseñas"], "observes": ["flujo"]},
 "evidence": [
  {"id": "E1", "kind": "OBSERVADO", "source": "conteo ficticio",
   "as_known_at": "2026-10-01", "value": {"entradas": 12}},
  {"id": "E2", "kind": "HIPOTESIS", "source": "relato ficticio",
   "as_known_at": "2026-10-01", "value": "vienen por el pan"}]
}
def response(visible):
 return {"schema_version": "cei.arena.v0.1", "case_id": "CAF-DEMO-001",
  "lane": visible["lane"], "snapshot_sha256": visible["snapshot_sha256"],
  "hypotheses": [
   {"id":"H1","mechanism":"esperas → abandonos","falsifier":"no hay abandonos",
    "evidence_ids":["E1"]}],
  "unknowns":["tiempos de espera"], "next_tests":[
   {"question":"¿hay abandono en picos?", "discriminates":["H1","alternativa"],
    "estimated_cost":0}],
  "cost":{"minutes":10}, "modelica_executed":False}

class ArenaTests(unittest.TestCase):
 def test_three_lanes_independent(self):
  hashes = [view_for_lane(CASE, lane)["snapshot_sha256"] for lane in
            ("A_CONVENCIONAL","B_SD_DETERMINISTA","C_IGC")]
  self.assertEqual(len(set(hashes)), 3)
 def test_no_holdout_leak(self):
  case = copy.deepcopy(CASE);case["gold"]={"true_mechanism":"H1"}
  with self.assertRaises(ValueError):view_for_lane(case,"C_IGC")
 def test_round_trip_never_auto_approves(self):
  visible = view_for_lane(CASE,"C_IGC")
  sealed = seal_submission(response(visible), visible)
  result = adjudicate(visible,sealed,holdout={"case_id":"CAF-DEMO-001","answer":"secret"})
  self.assertEqual(result["engineering"],"PASS")
  self.assertEqual(result["empirical"],"NOT_EVALUATED")
  self.assertEqual(result["gates"]["G1"],"NOT_ADJUDICATED")
  self.assertNotIn("answer",str(result))
 def test_tampering_rejected(self):
  visible=view_for_lane(CASE,"C_IGC")
  sealed=seal_submission(response(visible),visible)
  sealed["submission"]["unknowns"].append("alterado")
  with self.assertRaises(ValueError):adjudicate(visible,sealed)
 def test_invented_evidence_rejected(self):
  visible=view_for_lane(CASE,"C_IGC")
  bad=response(visible);bad["hypotheses"][0]["evidence_ids"]=["GOLD"]
  with self.assertRaises(ValueError):seal_submission(bad,visible)
 def test_constructor_cannot_self_grade(self):
  visible=view_for_lane(CASE,"C_IGC")
  bad=response(visible);bad["gates"]={"G1":"PASS"}
  with self.assertRaises(ValueError):seal_submission(bad,visible)
 def test_hash_deterministic(self):
  self.assertEqual(digest({"b":2,"a":1}),digest({"a":1,"b":2}))

if __name__=="__main__":
 unittest.main()
