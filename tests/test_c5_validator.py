#!/usr/bin/env python3
"""C5: independent reference acceptance and negative controls before DeepSeek calls."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from c5_validator import validate,validate_provider
FACTS=json.loads((ROOT/"experiments/c5/evaluation/facts.json").read_text())

def gold():
    stocks=[]
    for sid,start in FACTS["stock_initial"].items():
        ins=sum(f["total"] for f in FACTS["observed_flows"] if f["to"]==sid)
        outs=sum(f["total"] for f in FACTS["observed_flows"] if f["from"]==sid)
        stocks.append({"id":sid,"unit":FACTS["stock_unit"][sid],
                       "initial":start,"final":start+ins-outs})
    flows=[{"id":f"f{i+1}","entity":f["entity"],"from":f["from"],
            "to":f["to"],"unit":f["unit"],"total":f["total"]}
           for i,f in enumerate(FACTS["observed_flows"])]
    return {"stocks":stocks,"flows":flows,
            "feedback":[],"unknowns":["Desconocemos los instantes de cada préstamo"]}

class TestC5(unittest.TestCase):
    def invalid(self,fn,code):
        d=gold();fn(d)
        r=validate(d,FACTS)
        self.assertEqual(r["status"],"REJECT")
        self.assertIn(code,[g["id"] for g in r["gates"] if not g["pass"]])
        return r
    def test_gold(self):
        r=validate(gold(),FACTS)
        self.assertEqual(r["status"],"ACCEPT",r)
        self.assertEqual(r["score"],11)
        self.assertEqual({s["id"]:s["final"] for s in gold()["stocks"]},
                         {"available_copies":38,"loaned_copies":25,"repair_copies":4,"pending_reservations":7})
    def test_think_and_json(self):
        value="<think>Derivo el balance.</think>\n```json\n"+json.dumps(gold())+"\n```"
        d,reason,meta,out=validate_provider(value,FACTS)
        self.assertEqual(out["score"],11)
        self.assertEqual(reason,"Derivo el balance.")
        self.assertEqual(d,gold())
    def test_unclosed_reasoning(self):
        d,reason,meta,out=validate_provider("<think>x\n"+json.dumps(gold()),FACTS)
        self.assertEqual(out["status"],"FORMAT_REJECT")
    def test_invented_stock(self):
        self.invalid(lambda x:x["stocks"].append({"id":"returned_bin","unit":"copy","initial":0,"final":0}),"T2_STOCKS")
    def test_missing_repair_return(self):
        self.invalid(lambda x:x["flows"].pop(4),"T4_TOPOLOGY")
    def test_wrong_copy_units(self):
        self.invalid(lambda x:x["flows"][0].update(unit="reservation"),"T3_FLOW_TYPES")
    def test_wrong_reservation_entity(self):
        self.invalid(lambda x:x["flows"][6].update(entity="copy"),"T3_FLOW_TYPES")
    def test_loaned_incorrect_final(self):
        self.invalid(lambda x:next(s for s in x["stocks"] if s["id"]=="loaned_copies").update(final=99),"T7_STOCK_BALANCES")
    def test_pending_bad_final(self):
        self.invalid(lambda x:next(s for s in x["stocks"] if s["id"]=="pending_reservations").update(final=5),"T11_COVERAGE")
    def test_wrong_retirement_count(self):
        self.invalid(lambda x:x["flows"][5].update(total=2),"T5_PHYSICAL_COUNTS")
    def test_reservation_cancel_wrong(self):
        self.invalid(lambda x:x["flows"][8].update(total=2),"T6_RESERVATION_COUNTS")
    def test_double_count_reserve_as_checkout(self):
        self.invalid(lambda x:x["flows"][1].update(total=33),"T9_NO_DOUBLE_COUNT")
    def test_fictitious_feedback(self):
        self.invalid(lambda x:x["feedback"].append({"name":"loop","status":"observed","justification":"sin observaciones"}),"T10_EPISTEMIC")
    def test_blank_unknowns(self):
        self.invalid(lambda x:x.update(unknowns=[]),"T10_EPISTEMIC")
    def test_no_mutation(self):
        d=gold();before=json.dumps(d,sort_keys=True)
        validate(d,FACTS)
        self.assertEqual(before,json.dumps(d,sort_keys=True))
    def test_no_extra_root_fields(self):
        self.invalid(lambda x:x.update({"invented":123}),"T1_SCHEMA")
    def test_invalid_format(self):
        self.assertEqual(validate_provider("aquí: "+json.dumps(gold()),FACTS)[3]["status"],"FORMAT_REJECT")
if __name__=="__main__":unittest.main()
