#!/usr/bin/env python3
"""IGC-SL molecular topology compiler. LLM never authors executable math/code.

Only an evidence-bearing AST is accepted. An allowlisted template renders
Modelica classes/ports; values belong solely to the verified S2 Scenario.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROLES={
 "ACCEPTED_SOURCE":{"name":"accepted","class":"IGCMolecules.AcceptedSource","ports":{"out":("OUT","FLOW<Order>")},"facts":{"F1"}},
 "PREPARATION_QUEUE":{"name":"preparation","class":"IGCMolecules.BoundedQueue","ports":{"in":("IN","FLOW<Order>"),"out":("OUT","FLOW<PreparedOrder>"),"waiting":("OBSERVE","STATE<Order>")},"facts":{"F2"}},
 "DISPATCH_QUEUE":{"name":"dispatch","class":"IGCMolecules.BoundedQueue","ports":{"in":("IN","FLOW<PreparedOrder>"),"out":("OUT","FLOW<DeliveredOrder>"),"waiting":("OBSERVE","STATE<PreparedOrder>")},"facts":{"F3"}},
 "DELIVERY_COUNTER":{"name":"delivered","class":"IGCMolecules.DeliveryCounter","ports":{"in":("IN","FLOW<DeliveredOrder>"),"total":("OBSERVE","STATE<DeliveredOrder>")},"facts":{"F3"}}
}
REQUIRED_LINKS=[
 ("ACCEPTED_SOURCE","out","PREPARATION_QUEUE","in","F1"),
 ("PREPARATION_QUEUE","out","DISPATCH_QUEUE","in","F2"),
 ("DISPATCH_QUEUE","out","DELIVERY_COUNTER","in","F3")]
IDENTIFIER=re.compile(r"^[a-z][a-z0-9_]{0,23}$")

def load(name):
    return json.loads((HERE/name).read_text(encoding="utf-8"))

def parse_evidence(items,facts,eligible=None):
    if not isinstance(items,list) or not items:
        return False
    for item in items:
        if not isinstance(item,dict) or set(item)!={"fact_id","quote"}:
            return False
        fid=item["fact_id"];quote=item["quote"]
        if not isinstance(fid,str) or fid not in facts:
            return False
        if eligible and fid not in eligible:return False
        if not isinstance(quote,str) or len(quote.strip())<12 or quote not in facts[fid]:
            return False
    return True

def validate(proposal):
    issues=[]
    def fail(code,at,detail,repairable=True):
        issues.append({"code":code,"at":at,"detail":detail,"repairable":repairable})
    if not isinstance(proposal,dict) or set(proposal)!={"instances","links","unresolved"}:
        fail("S_SCHEMA","document","Exact keys: instances, links, unresolved")
        return {"status":"REPAIRABLE","issues":issues,"structure_accepted":False}
    if not isinstance(proposal["instances"],list) or len(proposal["instances"])>8:
        fail("S_INSTANCES","instances","Instances must be an array of at most eight entries")
        return {"status":"REPAIRABLE","issues":issues,"structure_accepted":False}
    if not isinstance(proposal["links"],list) or len(proposal["links"])>8:
        fail("S_LINKS","links","Links must be an array of at most eight entries")
        return {"status":"REPAIRABLE","issues":issues,"structure_accepted":False}
    if not isinstance(proposal["unresolved"],list) or len(proposal["unresolved"])>5 or not all(
            isinstance(s,str) and 1<=len(s)<=150 for s in proposal["unresolved"]):
        fail("S_UNRESOLVED","unresolved","Use a short list of unresolved structural facts")
    facts={f["id"]:f["text"] for f in load("case.json")["facts"]}
    instances={}
    by_module={}
    for i,item in enumerate(proposal["instances"]):
        where=f"instances[{i}]"
        if not isinstance(item,dict) or set(item)!={"id","module","evidence"}:
            fail("S_INSTANCE_SCHEMA",where,"Exact keys: id, module, evidence");continue
        rid,mid=item["id"],item["module"]
        if not isinstance(rid,str) or not IDENTIFIER.fullmatch(rid):
            fail("S_INSTANCE_ID",where,"Use lowercase ASCII alphanumeric IDs max 24");continue
        if rid in instances:
            fail("S_DUPLICATE_INSTANCE",where,"Instance ID already used");continue
        if not isinstance(mid,str) or mid not in ROLES:
            fail("M_UNKNOWN_MOLECULE",where,"Use only registered module IDs");continue
        if mid in by_module:
            fail("M_DUPLICATE_ROLE",where,"This v1 supports exactly one instance per molecular role");continue
        if not parse_evidence(item["evidence"],facts,ROLES[mid]["facts"]):
            fail("E_INSTANCE_UNGROUNDED",where,"Need an exact quote from one of the relevant facts")
        instances[rid]=mid
        by_module[mid]=rid
    for mid in ROLES:
        if mid not in by_module:
            fail("M_REQUIRED_ROLE_MISSING","instances",f"Missing evidence-backed molecule {mid}")
    actual=set()
    used_ports=set()
    for i,item in enumerate(proposal["links"]):
        where=f"links[{i}]"
        if not isinstance(item,dict) or set(item)!={"from","to","evidence"}:
            fail("S_LINK_SCHEMA",where,"Exact keys: from, to, evidence");continue
        first,last=item["from"],item["to"]
        if not isinstance(first,str) or not isinstance(last,str) or first.count(".")!=1 or last.count(".")!=1:
            fail("T_PORT_FORMAT",where,"Ports use instance_id.registered_port");continue
        a,ap=first.split(".");b,bp=last.split(".")
        if a not in instances or b not in instances:
            fail("T_UNKNOWN_INSTANCE",where,"Instance not found; refer to an existing instance ID");continue
        am,bm=instances[a],instances[b]
        pa=ROLES[am]["ports"].get(ap);pb=ROLES[bm]["ports"].get(bp)
        if pa is None or pb is None:
            fail("T_UNKNOWN_PORT",where,"Only catalog-defined ports can be connected");continue
        if pa[0]!="OUT" or pb[0]!="IN" or pa[1]!=pb[1]:
            fail("T_INCOMPATIBLE_PORT",where,"Connect OUT FLOW<T> to IN FLOW<T> of the same semantic entity");continue
        pair=(am,ap,bm,bp)
        expected=next((e for e in REQUIRED_LINKS if tuple(e[:4])==pair),None)
        if expected is None:
            fail("M_UNSUPPORTED_ROUTE",where,"Route is outside the verified S2 molecular composition");continue
        if pair in actual or (am,ap) in used_ports or (bm,bp) in used_ports:
            fail("T_DUPLICATE_OR_MULTICAST",where,"Material flow port already connected");continue
        if not parse_evidence(item["evidence"],facts,{expected[4]}):
            fail("E_LINK_UNGROUNDED",where,"Need literal supporting quote for this material transfer")
        actual.add(pair);used_ports.add((am,ap));used_ports.add((bm,bp))
    for a,ap,b,bp,fid in REQUIRED_LINKS:
        if (a,ap,b,bp) not in actual:
            fail("M_MISSING_MATERIAL_LINK","links",f"Missing {a}.{ap} -> {b}.{bp}")
    status="REPAIRABLE" if issues else "STRUCTURALLY_VALID"
    return {"status":status,"issues":issues,"structure_accepted":not issues,
            "validated_modules":sorted(by_module),"validated_material_links":len(actual),
            "numerical_inputs_visible_to_llm":False,
            "numerical_binding_source":"IGCS2MakeToOrder.Scenario (backend only)"}

def render(proposal):
    result=validate(proposal)
    if not result["structure_accepted"]:raise ValueError("REJECT_UNVALIDATED_STRUCTURE")
    # Module instances are mapped to FIXED internal identifiers. Not a character of
    # LLM-provided names, quotes or code is interpolated into executable Modelica.
    declarations=[
        "    IGCMolecules.AcceptedSource accepted;",
        "    IGCMolecules.BoundedQueue preparation(maxThroughput=capacityPreparing,responseTime=preparationResponseTime);",
        "    IGCMolecules.BoundedQueue dispatch(maxThroughput=capacityDispatch,responseTime=dispatchResponseTime);",
        "    IGCMolecules.DeliveryCounter delivered;"]
    lines=["within;","package IGCComposed",
        "  model Components",
        "    extends IGCS2MakeToOrder.Scenario;",
        *declarations,
        "  equation",
        "    accepted.externalRate = acceptedRate;"]
    native={
       ("ACCEPTED_SOURCE","PREPARATION_QUEUE"):"connect(accepted.outflow,preparation.arrival);",
       ("PREPARATION_QUEUE","DISPATCH_QUEUE"):"connect(preparation.completed,dispatch.arrival);",
       ("DISPATCH_QUEUE","DELIVERY_COUNTER"):"connect(dispatch.completed,delivered.arrival);"}
    instances={i["id"]:i["module"] for i in proposal["instances"]}
    for link in proposal["links"]:
        a=instances[link["from"].split(".")[0]]
        b=instances[link["to"].split(".")[0]]
        lines.append("    "+native[(a,b)])
    lines.extend([
        "    unpreparedOrders = preparation.waiting;",
        "    preparedOrders = dispatch.waiting;",
        "    deliveredOrders = delivered.total;",
        "    preparationRate = preparation.completed;",
        "    dispatchRate = dispatch.completed;",
        "  end Components;",
        '  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));',
        "end IGCComposed;",""])
    text="\n".join(lines)
    for disallowed in ("der(", "function ","import ", "system("):
        if disallowed in text:raise ValueError("UNTRUSTED_MODEL_SOURCE")
    return text

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--proposal",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--model",type=Path)
    a=p.parse_args()
    try:proposal=json.loads(a.proposal.read_text(encoding="utf-8"))
    except (ValueError,UnicodeError):proposal=None
    result=validate(proposal)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if a.model and result["structure_accepted"]:
        a.model.write_text(render(proposal),encoding="utf-8")
    print("IGC_MOLECULAR_COMPOSER",json.dumps(result,ensure_ascii=False),flush=True)
    if not result["structure_accepted"]:raise SystemExit(2)

if __name__=="__main__":main()
