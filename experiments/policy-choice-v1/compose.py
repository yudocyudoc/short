#!/usr/bin/env python3
"""Competing MTO/MTS architectures, identical abstract ports, no oracle gate.
This compiler validates structure and verbatim provenance, but NEVER chooses
between MTO and MTS by case labels. Original native models stay immutable.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
ALLOWED={"MTO":"IGCS2MakeToOrder.Components","MTS":"IGCS1Parity.Components"}
IDS=re.compile(r"^[a-z][a-z0-9_]{0,19}$")
TYPES={"SOURCE":{"out":"FLOW<Order>"},
       "MTO":{"in":"FLOW<Order>","out":"FLOW<DeliveredOrder>"},
       "MTS":{"in":"FLOW<Order>","out":"FLOW<DeliveredOrder>"},
       "SINK":{"in":"FLOW<DeliveredOrder>"}}
def read(f):return json.loads((HERE/f).read_text(encoding="utf-8"))
def load_case(cid):
    return next(c for c in read("cases.json")["cases"] if c["id"]==cid)
def verbatim(ev,facts):
    return isinstance(ev,dict) and set(ev)=={"fact_id","quote"} and isinstance(ev["fact_id"],str) and ev["fact_id"] in facts and isinstance(ev["quote"],str) and len(ev["quote"].strip())>=24 and ev["quote"] in facts[ev["fact_id"]]
def validate(cid,proposal):
    issues=[]
    def error(code,at):issues.append({"code":code,"location":at})
    if not isinstance(proposal,dict) or set(proposal)!={"decision","policy","instances","links","support","counterevidence","unresolved"}:
        return {"status":"INVALID_SCHEMA","issues":[{"code":"S_SCHEMA"}],"executable":False}
    decision=proposal["decision"]
    if decision not in ("COMPOSE","PARTIAL","ABSTAIN"):error("S_DECISION","decision")
    facts={f["id"]:f["text"] for f in load_case(cid)["facts"]}
    for field in ("support","counterevidence"):
        if not isinstance(proposal[field],list) or any(not verbatim(x,facts) for x in proposal[field]):
            error("E_QUOTE_INVALID",field)
    if not isinstance(proposal["unresolved"],list) or any(not isinstance(x,str) or not x.strip() or len(x)>240 for x in proposal["unresolved"]):
        error("S_UNRESOLVED","unresolved")
    nodes=proposal["instances"];links=proposal["links"]
    if not isinstance(nodes,list) or len(nodes)>5 or not isinstance(links,list) or len(links)>4:
        error("S_GRAPH","graph");nodes=[];links=[]
    if decision in ("ABSTAIN","PARTIAL"):
        if proposal["policy"] is not None:error("M_PARTIAL_WITH_POLICY","policy")
        if decision=="ABSTAIN" and (nodes or links):error("M_ABSTAIN_WITH_GRAPH","graph")
        if not proposal["unresolved"]:error("E_UNRESOLVED_REQUIRED","unresolved")
        if issues:return {"status":"REJECTED","issues":issues,"executable":False}
        return {"status":decision,"issues":[],"executable":False}
    if proposal["policy"] not in ALLOWED:
        error("M_UNSUPPORTED_POLICY","policy")
    if not proposal["support"]:
        error("E_POLICY_SUPPORT_MISSING","support")
    if not proposal["counterevidence"]:
        error("E_RIVAL_EXCLUSION_MISSING","counterevidence")
    if proposal["unresolved"]:
        error("E_UNRESOLVED_BUT_COMPOSED","unresolved")
    ids={};roles={}
    for n in nodes:
        if not isinstance(n,dict) or set(n)!={"id","module","evidence"}:
            error("S_NODE","instances");continue
        nid,mid=n["id"],n["module"]
        if not isinstance(nid,str) or not IDS.fullmatch(nid) or nid in ids:
            error("S_NODE_ID","instances");continue
        if mid not in ("SOURCE","MTO","MTS","SINK"):
            error("M_UNKNOWN_MODULE","instances");continue
        if mid in roles:error("M_DUPLICATE_ROLE","instances")
        if not verbatim(n["evidence"],facts):error("E_NODE_QUOTE","instances")
        ids[nid]=mid;roles[mid]=nid
    if set(roles)!={"SOURCE",proposal["policy"],"SINK"}:error("M_GRAPH_ROLES","instances")
    edge_set=set()
    for link in links:
        if not isinstance(link,dict) or set(link)!={"from","to","evidence"}:
            error("S_EDGE","links");continue
        source,target=link["from"],link["to"]
        if not isinstance(source,str) or not isinstance(target,str) or source.count(".")!=1 or target.count(".")!=1:
            error("T_PORT_FORMAT","links");continue
        a,ap=source.split(".");b,bp=target.split(".")
        if a not in ids or b not in ids:
            error("T_INSTANCE_UNKNOWN","links");continue
        sig_a=TYPES[ids[a]].get(ap);sig_b=TYPES[ids[b]].get(bp)
        if sig_a is None or sig_b is None or sig_a!=sig_b or ap!="out" or bp!="in":
            error("T_WRONG_PORT","links");continue
        pair=(ids[a],ids[b])
        if pair in edge_set:error("T_DUPLICATED_LINK","links")
        edge_set.add(pair)
        if not verbatim(link["evidence"],facts):error("E_LINK_QUOTE","links")
    if edge_set!={("SOURCE",proposal["policy"]),(proposal["policy"],"SINK")}:
        error("M_GRAPH_NOT_CONNECTED","links")
    if issues:return {"status":"REJECTED","issues":issues,"executable":False}
    return {"status":"STRUCTURALLY_VALID","issues":[],"executable":True,
      "chosen_policy":proposal["policy"],"equations_from_llm":0,
      "typing_alone_determines_policy":False}
def render(cid,proposal):
    chk=validate(cid,proposal)
    if not chk["executable"]:raise ValueError("ONLY_VALID_GRAPH_CAN_RENDER")
    # Zero characters from LLM instances/links/evidence appear in code.
    # Selecting one previously compiled native model is the *only* backend operation.
    clazz=ALLOWED[chk["chosen_policy"]]
    return "\n".join(["within;","package IGCSelected",
        "  model Candidate",
        "    extends "+clazz+";",
        "  end Candidate;",
        "end IGCSelected;",""])
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--case",required=True)
    p.add_argument("--proposal",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--model",type=Path)
    args=p.parse_args()
    try:x=json.loads(args.proposal.read_text(encoding="utf-8"))
    except (ValueError,UnicodeError):x=None
    result=validate(args.case,x)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if args.model and result["executable"]:args.model.write_text(render(args.case,x),encoding="utf-8")
    print("POLICY_COMPOSER",json.dumps({"case":args.case,**result}),flush=True)
    if result["status"] in ("INVALID_SCHEMA","REJECTED"):raise SystemExit(2)
if __name__=="__main__":main()
