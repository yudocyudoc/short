#!/usr/bin/env python3
"""IGC-0 contract v2: explicit mechanism coverage + typed SD semantics.

Frozen BEFORE M01 v2 inference; applies old source checks AND new contracts.
An acceptance is *only* structural/epistemic, not causal adjudication.
"""
from semantic_audit import audit as original_audit, family
from igc import all_evidence_refs

ROLES={"shared_kitchen","order_backlog","delivery_dispatch","payout_delay"}
STATES={"represented","hypothesis","unknown"}
FACT_LABELS={"OBSERVADO","CALIBRADO","INFERIDO"}
REF_CATEGORIES={"OBSERVADO","CALIBRADO"}
ACTIONS={"no_delivery","open_full","open_offpeak_capped"}

def audit_v2(model,packet):
    old=original_audit(model,packet)
    issues=list(old["issues"])
    def fail(code,location,message):
        issues.append({"code":code,"where":location,"detail":message})
    if not isinstance(model,dict):
        return {"accepted":False,"issues":issues,"validator":"IGC0_SEMANTIC_V2"}
    sources=all_evidence_refs(packet)
    def references(refs,where,require=False):
        if not isinstance(refs,list):
            fail("INVALID_REFS",where,"References must be an array")
            return []
        if require and not refs:
            fail("NO_EVIDENCE",where,"At least one reference required")
        seen=[]
        for ref in refs:
            if not isinstance(ref,dict):
                fail("INVALID_REFS",where,"Invalid reference object")
                continue
            label=sources.get((ref.get("source_id"),ref.get("sha256")))
            if not label:
                fail("UNVERIFIED_REF",where,"Source id/hash absent from public packet")
            seen.append(label)
        return seen
    stocks=model.get("stocks",[])
    pipes=model.get("pipes",[])
    if not isinstance(stocks,list) or not isinstance(pipes,list):
        return {"accepted":False,"issues":issues,"validator":"IGC0_SEMANTIC_V2"}
    stock_ids={s.get("id") for s in stocks if isinstance(s,dict)}
    pipe_ids={p.get("id") for p in pipes if isinstance(p,dict)}
    node_ids=stock_ids|pipe_ids
    for s in stocks:
        if not isinstance(s,dict):continue
        sid=s.get("id")
        lab=s.get("initial_label")
        ini=s.get("initial")
        refs=references(s.get("initial_refs",[]),"stock:"+str(sid), lab in FACT_LABELS and ini is not None)
        if lab=="DESCONOCIDO" and ini is not None:
            fail("UNKNOWN_STOCK_NUMBER",sid,"Unknown stock cannot have a numeric initial")
        if lab in REF_CATEGORIES and ini is not None and refs and lab not in refs:
            fail("STOCK_SOURCE_LABEL",sid,"Stock initial label conflicts with source epistemic type")
    for p in pipes:
        if not isinstance(p,dict):continue
        pid=p.get("id")
        lab=p.get("epistemic")
        refs=references(p.get("evidence_refs",[]),"pipe:"+str(pid),lab in FACT_LABELS)
        if lab in REF_CATEGORIES and refs and lab not in refs:
            fail("PIPE_SOURCE_LABEL",pid,"Observed/calibrated pipe lacks source of declared category")
        cap=p.get("capacity_source")
        if cap is not None:
            if not isinstance(cap,dict):
                fail("INVALID_CAPACITY_SOURCE",pid,"capacity_source must be one source/hash pair or null")
            else:
                label=sources.get((cap.get("source_id"),cap.get("sha256")))
                if not label:
                    fail("UNVERIFIED_CAPACITY",pid,"Capacity is not backed by a known source")
    links=model.get("informational_links")
    if not isinstance(links,list):
        fail("MISSING_INFORMATIONAL_LINKS","informational_links","Must supply distinct informational_links list")
    else:
        for n,link in enumerate(links):
            if not isinstance(link,dict):
                fail("INVALID_INFORMATIONAL_LINK",str(n),"Link must be an object")
                continue
            if link.get("type")!="information" or not str(link.get("why","")).strip():
                fail("INVALID_INFORMATIONAL_LINK",str(n),"Only justified nontransfer informational links")
            if link.get("from") not in node_ids or link.get("to") not in node_ids:
                fail("DANGLING_INFORMATIONAL_LINK",str(n),"Both ends must match a declared stock or pipe id")
    contrast=model.get("contrast")
    if isinstance(contrast,list):
        for n,c in enumerate(contrast):
            if not isinstance(c,dict):continue
            k="contrast:"+str(n)
            refs=references(c.get("evidence_refs",[]),k,True)
            if c.get("pipe_or_mechanism_id") not in node_ids:
                fail("UNLINKED_CONTRAST",k,"Contrast must refer to a declared stock/pipe")
            if not str(c.get("explanation","")).strip():
                fail("EMPTY_CONTRAST",k,"Explain calibrated vs observed and limits")
            if c.get("type")=="none" and c.get("epistemic") in ("DESCONOCIDO","HIPÓTESIS"):
                fail("UNSUPPORTED_NO_DEVIATION",k,"Insufficient data cannot prove absence of deviation")
            if c.get("epistemic") in REF_CATEGORIES and refs and c["epistemic"] not in refs:
                fail("CONTRAST_SOURCE_LABEL",k,"Contrast source label unsupported")
    checks=model.get("mechanism_checks")
    if not isinstance(checks,list):
        fail("MISSING_MECHANISM_CHECKS","mechanism_checks","Four explicit mechanism assessments required")
        checks=[]
    roles=[c.get("role") for c in checks if isinstance(c,dict)]
    if len(checks)!=4 or len(roles)!=4 or set(roles)!=ROLES:
        fail("MECHANISM_ROLES","mechanism_checks","Expected four distinct standard mechanisms")
    counts={"represented":0,"hypothesis":0,"unknown":0}
    for c in checks:
        if not isinstance(c,dict):
            fail("MECHANISM_SCHEMA","mechanism_checks","Each assessment must be an object")
            continue
        role=c.get("role")
        st=c.get("status")
        if st not in STATES:
            fail("MECHANISM_STATUS",role,"Use represented, hypothesis or unknown")
            continue
        counts[st]+=1
        if not str(c.get("explanation","")).strip():
            fail("MECHANISM_EXPLANATION",role,"Explain what can or cannot be inferred")
        linked=c.get("linked_ids")
        if not isinstance(linked,list):
            fail("MECHANISM_LINKS",role,"linked_ids must be a list")
            linked=[]
        if st=="represented" and not linked:
            fail("UNLINKED_REPRESENTED_MECHANISM",role,"A represented mechanism must map to graph")
        for target in linked:
            if target not in node_ids:
                fail("MECHANISM_DANGLING_LINK",role,"Unknown graph id in linked_ids")
        references(c.get("evidence_refs",[]),"mechanism:"+str(role),st=="represented")
    ident=model.get("identifiability",{})
    if isinstance(ident,dict) and ident.get("status")=="identifiable":
        if not isinstance(contrast,list) or not any(
           isinstance(c,dict) and c.get("type")=="difference" and
           c.get("epistemic") in ("OBSERVADO","INFERIDO") and c.get("evidence_refs")
           for c in contrast):
            fail("UNSUPPORTED_IDENTIFIABLE","identifiability","Requires empirical, sourced difference")
    if model.get("scenario_projections")!=[]:
        fail("UNVALIDATED_PROJECTION","scenario_projections","Keep empty until the aggregate SD model is calibrated")
    decision=model.get("decision")
    if not isinstance(decision,dict) or decision.get("choice")!="abstain":
        fail("UNSUPPORTED_DECISION","decision","Current pilot requires abstention")
    actions=model.get("actions")
    if not isinstance(actions,list) or set(actions)!=ACTIONS or len(actions)!=3:
        fail("ACTIONS","actions","Expected three admissible policies")
    return {"accepted":not issues,"issues":issues,"validator":"IGC0_SEMANTIC_V2",
            "stock_count":len(stocks),"pipe_count":len(pipes),
            "contrast_count":len(contrast) if isinstance(contrast,list) else 0,
            "mechanism_status_counts":counts}
