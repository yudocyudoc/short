#!/usr/bin/env python3
"""C4 strict SD graph validator, with independent balance gates.

Transport normalization is ONLY removal of one enclosing Markdown JSON fence.
Content, calculations and graph edges are NEVER repaired.
"""
import json
import re
from pathlib import Path
import sys

GATES=["G1_SCHEMA","G2_STOCKS","G3_FLOW_TYPES","G4_TOPOLOGY",
       "G5_REQUEST_COUNTS","G6_PENDING","G7_INVENTORY","G8_CAPACITY",
       "G9_COUPLING","G10_EPISTEMIC"]
KEYS={"horizon_hours","stocks","flows","capacity","feedback","unknowns"}
CAP_KEYS={"machine_per_hour","machine_period_max","material_period_max",
          "joint_period_max","observed_prepared"}
STOCK_UNITS={"inventory":"beverage_equivalent","accepted_pending":"request"}
FLOW_UNITS={"request":"request","material":"beverage_equivalent"}
FENCE=re.compile(r"^\s*```(?:json)?\s*\n(?P<body>.*)\n```\s*$",re.I|re.S)

def amount(x):
    return type(x) is int and x>=0

def load_transport(raw):
    if not isinstance(raw,str):
        return None,{"stripped_fence":False,"format":"invalid_nontext"}
    original=raw
    m=FENCE.fullmatch(raw)
    if m:
        raw=m.group("body")
    try:
        obj=json.loads(raw)
    except (ValueError, TypeError):
        return None,{"stripped_fence":bool(m),"format":"non_json"}
    return obj,{"stripped_fence":bool(m),"format":"single_fenced_json" if m else "json"}

def outcome(passes, explanations, transport=None):
    score=sum(bool(passes.get(x)) for x in GATES)
    o={"status":"ACCEPT" if score==10 else "REJECT","score":score,"maximum":10,
       "gates":[{"id":name,"pass":bool(passes.get(name)),
                 "reason":None if passes.get(name) else explanations.get(name,"Invalid or unavailable")} for name in GATES]}
    if transport is not None:
        o["transport"]=transport
    return o

def validate_model(obj, facts):
    passed={k:False for k in GATES}
    why={}
    def test(k,valid,why_text):
        passed[k]=bool(valid)
        if not valid: why[k]=why_text

    if not isinstance(obj,dict) or set(obj)!=KEYS:
        test("G1_SCHEMA",False,"JSON object has missing or extra root keys")
        return outcome(passed,why)
    stocks,flows,cap,feedback,unknowns=(obj[k] for k in ("stocks","flows","capacity","feedback","unknowns"))
    stock_schema=(isinstance(stocks,list) and all(
        isinstance(s,dict) and set(s)=={"id","unit","initial","final"} and
        isinstance(s["id"],str) and s["id"] and isinstance(s["unit"],str) and
        amount(s["initial"]) and amount(s["final"]) for s in stocks))
    flow_schema=(isinstance(flows,list) and all(
        isinstance(t,dict) and set(t)=={"id","entity","from","to","total","unit"} and
        all(isinstance(t[k],str) and bool(t[k]) for k in ("id","entity","from","to","unit"))
        and amount(t["total"]) for t in flows))
    cap_schema=(isinstance(cap,dict) and set(cap)==CAP_KEYS and all(amount(v) for v in cap.values()))
    feedback_schema=(isinstance(feedback,list) and all(
        isinstance(f,dict) and set(f)=={"name","status","justification"}
        and all(isinstance(f[k],str) for k in f) for f in feedback))
    unknown_schema=isinstance(unknowns,list) and all(isinstance(v,str) for v in unknowns)
    test("G1_SCHEMA",amount(obj["horizon_hours"]) and stock_schema and flow_schema
         and cap_schema and feedback_schema and unknown_schema,
         "Invalid JSON field types, totals, arrays or schema")
    if not passed["G1_SCHEMA"]:
        return outcome(passed,why)

    # Duplicates are failures; balances below still check independently.
    sids=[s["id"] for s in stocks]; fmap={s["id"]:s for s in stocks}
    test("G2_STOCKS",len(stocks)==2 and len(set(sids))==len(stocks) and
         set(sids)==set(STOCK_UNITS) and
         all(fmap[k]["unit"]==STOCK_UNITS[k] for k in STOCK_UNITS)
         and fmap["inventory"]["initial"]==facts["initial_inventory"]
         and fmap["accepted_pending"]["initial"]==facts["initial_pending"],
         "Stocks must be inventory and accepted_pending only, with typed initial quantities")

    ids=[t["id"] for t in flows]
    typed=all(t["entity"] in FLOW_UNITS and t["unit"]==FLOW_UNITS.get(t["entity"]) for t in flows)
    test("G3_FLOW_TYPES",len(flows)==6 and len(set(ids))==6 and typed,
         "Require six unique flows with entity/unit compatibility")

    req=[t for t in flows if t["entity"]=="request"]
    mat=[t for t in flows if t["entity"]=="material"]
    edges_req=[(t["from"],t["to"]) for t in req]
    edges_mat=[(t["from"],t["to"]) for t in mat]
    allowed_req={tuple(e) for e in facts["allowed_request_edges"]}
    allowed_mat={tuple(e) for e in facts["allowed_material_edges"]}
    test("G4_TOPOLOGY",len(req)==5 and len(mat)==1 and len(set(edges_req))==5
         and set(edges_req)==allowed_req and set(edges_mat)==allowed_mat,
         "Request/material transitions must follow the allowed state order without extra edges")

    qty_req={(t["from"],t["to"]):t["total"] for t in req}
    qty_mat={(t["from"],t["to"]):t["total"] for t in mat}
    def q(origin,dest):
        return qty_req.get((origin,dest))
    received=q("external","submitted")
    accepted=q("submitted","accepted_pending")
    rejected=q("submitted","rejected")
    canceled=q("accepted_pending","canceled")
    fulfilled=q("accepted_pending","fulfilled")
    consumed=qty_mat.get(("inventory","consumed"))
    wanted_accepted=facts["requests_total"]-facts["rejected_before_acceptance"]
    expected_req={"external":facts["requests_total"],"accepted":wanted_accepted,
                  "rejected":facts["rejected_before_acceptance"],
                  "canceled":facts["canceled_after_acceptance"],"fulfilled":facts["prepared_delivered"]}
    test("G5_REQUEST_COUNTS",
         received==expected_req["external"] and accepted==expected_req["accepted"]
         and rejected==expected_req["rejected"] and canceled==expected_req["canceled"]
         and fulfilled==expected_req["fulfilled"] and all(v is not None for v in
         (received,accepted,rejected,canceled,fulfilled)) and received==accepted+rejected,
         "Request event totals and exhaustive partition contradict supplied observations")

    # Independent of G2! Check quantity of each stock when present, even if extra stock exists.
    pen=fmap.get("accepted_pending")
    expected_pen=facts["initial_pending"]+wanted_accepted-facts["canceled_after_acceptance"]-facts["prepared_delivered"]
    test("G6_PENDING",bool(pen) and pen["unit"]=="request"
         and pen["initial"]==facts["initial_pending"]
         and pen["final"]==expected_pen
         and all(v is not None for v in (accepted,canceled,fulfilled))
         and pen["final"]==pen["initial"]+accepted-canceled-fulfilled,
         "Pending stock final disagrees with accepted, canceled and fulfilled event flows")

    inv=fmap.get("inventory")
    expected_inv=facts["initial_inventory"]+facts["replenishment"]-facts["other_material_outflows"]-facts["prepared_delivered"]
    test("G7_INVENTORY",bool(inv) and inv["unit"]=="beverage_equivalent"
         and inv["initial"]==facts["initial_inventory"] and consumed==facts["prepared_delivered"]
         and inv["final"]==expected_inv and inv["final"]==inv["initial"]+facts["replenishment"]
         -facts["other_material_outflows"]-consumed,
         "Inventory final and material consumption disagree with stated stock balance")

    machine_total=facts["horizon_hours"]*facts["machine_capacity_per_hour"]
    material_total=facts["initial_inventory"]+facts["replenishment"]
    test("G8_CAPACITY",obj["horizon_hours"]==facts["horizon_hours"]
         and cap["machine_per_hour"]==facts["machine_capacity_per_hour"]
         and cap["machine_period_max"]==machine_total
         and cap["material_period_max"]==material_total
         and cap["joint_period_max"]==min(machine_total,material_total)
         and cap["observed_prepared"]==facts["prepared_delivered"],
         "Machine, material, joint bound or observed preparation incorrect")

    test("G9_COUPLING",consumed is not None and fulfilled is not None
         and consumed==fulfilled==cap["observed_prepared"]
         and "prepared_stock" not in sids,
         "Material units, fulfilled requests or unpermitted ready-product stock conflict")
    test("G10_EPISTEMIC",bool(unknowns) and all(x.strip() for x in unknowns)
         and all(f["status"]=="hypothesis" and f["name"].strip()
                 and f["justification"].strip() for f in feedback),
         "Unknowns required; no observed feedback loop justified by scenario")
    return outcome(passed,why)

def validate_raw(raw,facts):
    obj,transport=load_transport(raw)
    if obj is None:
        p={k:False for k in GATES}
        return outcome(p,{"G1_SCHEMA":"Response is not JSON nor a single wrapped JSON code block"},transport)
    r=validate_model(obj,facts)
    r["transport"]=transport
    return r

def compact_feedback(report):
    return [{"id":g["id"],"reason":g["reason"]} for g in report["gates"] if not g["pass"]]

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("Usage: python scripts/c4_validator.py answer.txt facts.json")
    r=validate_raw(Path(sys.argv[1]).read_text(encoding="utf-8"),
                   json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")))
    print(json.dumps(r,indent=2,ensure_ascii=False))
    raise SystemExit(0 if r["status"]=="ACCEPT" else 1)
