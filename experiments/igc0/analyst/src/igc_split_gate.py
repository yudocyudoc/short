#!/usr/bin/env python3
"""IGC-0 split protocol: independent gate for I/G, then evidence-gated contrast.

A graph cannot pass just because it parses. C is never called on a rejected graph.
Source IDs are verified from the public packet; no oracle or reference scaffold used.
"""
from prepare import sha
from igc import validate_model, all_evidence_refs
from semantic_audit import audit as prior_semantic, family
from semantic_audit_v2 import audit_v2,ROLES,STATES

GRAPH_KEYS={"case_id","stocks","pipes","informational_links","boundary","mechanism_checks","unknowns"}
CONTRAST_KEYS={"case_id","graph_sha256","contrast","identifiability","actions","decision","scenario_projections","unknowns"}
CATEGORIES={"orders":"order","meals_equivalent":"meal","MXN":"money"}
LABELS={"OBSERVADO","CALIBRADO","INFERIDO","HIPÓTESIS","DESCONOCIDO"}

def graph_gate(model,packet):
    issues=[]
    def err(code,location,message):
        issues.append({"code":code,"where":str(location),"detail":message})
    if not isinstance(model,dict):
        return {"accepted":False,"issues":[{"code":"GRAPH_NOT_OBJECT","where":"root","detail":"Expected JSON object"}]}
    if set(model)!=GRAPH_KEYS:
        err("GRAPH_SCHEMA","root","Graph-only output must use exactly the seven graph fields")
    if model.get("case_id")!=packet.get("case_id"):
        err("CASE_ID","case_id","Wrong world")
    stocks=model.get("stocks")
    pipes=model.get("pipes")
    if not isinstance(stocks,list) or not isinstance(pipes,list) or not stocks or not pipes:
        err("GRAPH_EMPTY","root","Nonempty stocks and pipes required")
        return {"accepted":False,"issues":issues}
    if any(not isinstance(s,dict) for s in stocks) or any(not isinstance(p,dict) for p in pipes):
        err("GRAPH_TYPES","root","Stocks and pipes must contain objects")
        return {"accepted":False,"issues":issues}
    if len({s.get("id") for s in stocks})!=len(stocks):
        err("DUPLICATE_STOCK","stocks","Duplicate stock IDs")
    if len({p.get("id") for p in pipes})!=len(pipes):
        err("DUPLICATE_PIPE","pipes","Duplicate pipe IDs")
    stock_ids={s.get("id") for s in stocks}
    pipe_ids={p.get("id") for p in pipes}
    graph_ids=stock_ids|pipe_ids
    detected_families={family(s.get("unit")) for s in stocks}
    if not {"order","meal","money"}.issubset(detected_families):
        err("MISSING_DOMAIN_STOCK","stocks","Represent order, material and money accumulations; unknown initial can be null")
    known=all_evidence_refs(packet)
    for s in stocks:
        sid=s.get("id")
        if s.get("initial_label") not in LABELS:
            err("STOCK_LABEL",sid,"Invalid initial evidence label")
        initial=s.get("initial")
        refs=s.get("initial_refs",[])
        if initial is not None and (type(initial) not in (int,float)):
            err("INITIAL_TYPE",sid,"Initial must be numeric or null")
        if initial is None and s.get("initial_label")!="DESCONOCIDO":
            err("NULL_INITIAL_LABEL",sid,"Null initial must be DESCONOCIDO")
        if initial is not None and s.get("initial_label")=="DESCONOCIDO":
            err("UNKNOWN_INITIAL_ASSIGNED",sid,"Do not assign an unknown initial")
        if not isinstance(refs,list):
            err("STOCK_REFS",sid,"Source list required")
            continue
        if initial is not None and not refs:
            err("UNSUPPORTED_INITIAL",sid,"Numeric initial must cite a source")
        for ref in refs:
            if not isinstance(ref,dict):
                err("BAD_SOURCE",sid,"Reference must be an object")
                continue
            kind=known.get((ref.get("source_id"),ref.get("sha256")))
            if not kind:err("UNKNOWN_SOURCE",sid,"Reference id/hash not found")
            if s.get("initial_label") in ("OBSERVADO","CALIBRADO") and kind and kind!=s["initial_label"]:
                err("INITIAL_SOURCE_KIND",sid,"Declared initial type differs from source")
    for p in pipes:
        pid=p.get("id")
        if p.get("epistemic") not in LABELS:
            err("PIPE_EPISTEMIC",pid,"Unknown pipe label")
        refs=p.get("evidence_refs",[])
        if not isinstance(refs,list):
            err("PIPE_REFS",pid,"Evidence references must be list")
            continue
        if p.get("epistemic") in ("OBSERVADO","CALIBRADO","INFERIDO") and not refs:
            err("UNSUPPORTED_PIPE",pid,"Factual/derived pipes require sources")
        for ref in refs:
            if not isinstance(ref,dict):
                err("PIPE_REF_TYPE",pid,"Reference must be an object")
                continue
            kind=known.get((ref.get("source_id"),ref.get("sha256")))
            if not kind:err("UNKNOWN_PIPE_SOURCE",pid,"Source id/hash invalid")
            if p.get("epistemic") in ("OBSERVADO","CALIBRADO") and kind and kind!=p["epistemic"]:
                err("PIPE_SOURCE_KIND",pid,"Declared pipe epistemic category conflicts with source")
        source=p.get("capacity_source")
        if source is not None and (not isinstance(source,dict) or
            not known.get((source.get("source_id"),source.get("sha256")))):
            err("UNVERIFIED_CAPACITY",pid,"Capacity source not found")
        if p.get("from")==p.get("to"):
            err("SELF_PIPE",pid,"Trivial self pipe cannot encode transport")
        ends=[k for k in ("from","to") if p.get(k) in stock_ids]
        if not ends:
            err("DISCONNECTED_PIPE",pid,"Pipe must incidentally touch at least one declared stock")
        for side in ends:
            sid=p[side]
            stock=next(s for s in stocks if s.get("id")==sid)
            if family(p.get("unit_per_time"))!=family(stock.get("unit")):
                err("UNIT_MISMATCH",pid,"Pipe rate entity must equal stock entity")
        if len(ends)==2:
            a=next(s for s in stocks if s.get("id")==p["from"])
            b=next(s for s in stocks if s.get("id")==p["to"])
            if family(a.get("unit"))!=family(b.get("unit")):
                err("CROSS_DOMAIN_STOCK_FLOW",pid,"A pipe cannot directly transfer food into money")
    boundary=model.get("boundary")
    if not isinstance(boundary,dict) or not all(
        isinstance(boundary.get(k),list) and boundary[k] and all(isinstance(v,str) for v in boundary[k])
        for k in ("inside","outside","possible_omissions")):
        err("BOUNDARY","boundary","Explicit inside/outside/possible omissions required")
    links=model.get("informational_links")
    if not isinstance(links,list):
        err("INFORMATION_LINK_SCHEMA","informational_links","List required")
        links=[]
    for i,link in enumerate(links):
        if not isinstance(link,dict) or link.get("type")!="information" or not str(link.get("why","")).strip():
            err("INFORMATION_LINK",i,"Only typed nontransfer informational links with reason")
            continue
        if link.get("from") not in graph_ids or link.get("to") not in graph_ids:
            err("DANGLING_INFO_LINK",i,"Informational link must refer to declared stock/pipe IDs")
    checks=model.get("mechanism_checks")
    if not isinstance(checks,list):
        err("MECHANISM_CHECKS","mechanism_checks","Four roles required")
        checks=[]
    if len(checks)!=4 or any(not isinstance(c,dict) for c in checks) or {c.get("role") for c in checks if isinstance(c,dict)}!=ROLES:
        err("MECHANISM_ROLES","mechanism_checks","Exactly four unique domain roles")
    represented=0
    for c in checks:
        if not isinstance(c,dict):continue
        role=c.get("role")
        status=c.get("status")
        if status not in STATES:
            err("MECHANISM_STATUS",role,"Use represented, hypothesis or unknown")
            continue
        if not str(c.get("explanation","")).strip():
            err("MECHANISM_EXPLANATION",role,"Must explain epistemic status")
        ids=c.get("linked_ids")
        if not isinstance(ids,list):
            err("MECHANISM_LINKS",role,"linked_ids list required")
            ids=[]
        if status=="represented":
            represented+=1
            if not ids:err("UNLINKED_MECHANISM",role,"Represented must link to graph")
        if any(t not in graph_ids for t in ids):
            err("MECHANISM_DANGLING_LINK",role,"Unrecognized stock/pipe")
        refs=c.get("evidence_refs")
        if not isinstance(refs,list) or (status=="represented" and not refs):
            err("MECHANISM_REFS",role,"Represented mechanism requires evidence references")
            continue
        for ref in refs:
            if not isinstance(ref,dict) or not known.get((ref.get("source_id"),ref.get("sha256"))):
                err("MECHANISM_SOURCE",role,"Unknown evidence ID/hash")
    unknowns=model.get("unknowns")
    if not isinstance(unknowns,list) or not unknowns or any(not isinstance(x,str) or not x.strip() for x in unknowns):
        err("UNKNOWN_DECLARATION","unknowns","At least one substantive unknown is required")
    # Preserve preexisting provenance validation, but stage IG deliberately has NO contrast yet.
    pseudo={**model,"contrast":[],"identifiability":{"status":"insufficient_data"},
        "actions":["no_delivery","open_full","open_offpeak_capped"],
        "decision":{"choice":"abstain","reason":"No SD calibration","assumptions":[]},
        "scenario_projections":[]}
    old=validate_model(pseudo,packet)
    for issue in old.get("issues",[]):
        err("BASE_"+issue["code"],"baseline",issue["reason"])
    prior=prior_semantic(pseudo,packet)
    for issue in prior.get("issues",[]):
        if issue["code"]!="MISSING_IGC_CONTRAST":
            err("PRIOR_"+issue["code"],issue["where"],issue["detail"])
    return {"accepted":not issues,"issues":issues,"graph_sha256":sha(model),
            "stock_count":len(stocks),"pipe_count":len(pipes),
            "represented_mechanisms":represented,"validator":"IGC0_GRAPH_GATE_V3"}

def contrast_gate(contrast,graph,packet):
    issues=[]
    def err(code,where,message):
        issues.append({"code":code,"where":str(where),"detail":message})
    if not isinstance(contrast,dict):
        return {"accepted":False,"issues":[{"code":"CONTRAST_NOT_OBJECT","where":"root","detail":"Expected JSON object"}]}
    if set(contrast)!=CONTRAST_KEYS:
        err("CONTRAST_SCHEMA","root","Contrast-only output must use exactly seven fields")
    if contrast.get("case_id")!=packet.get("case_id"):
        err("CASE_ID","case_id","Wrong case")
    if contrast.get("graph_sha256")!=sha(graph):
        err("GRAPH_HASH","graph_sha256","Must cite exact accepted graph hash")
    for field in ("stocks","pipes","informational_links","boundary","mechanism_checks"):
        if field in contrast:err("GRAPH_MUTATION",field,"Contrast must not alter graph structure")
    cl=contrast.get("contrast")
    if not isinstance(cl,list) or not cl:
        err("EMPTY_CONTRAST","contrast","Explicit comparison required")
        cl=[]
    source_map=all_evidence_refs(packet)
    ids={s.get("id") for s in graph["stocks"]}|{p.get("id") for p in graph["pipes"]}
    for i,c in enumerate(cl):
        if not isinstance(c,dict):
            err("CONTRAST_TYPE",i,"Entries must be objects")
            continue
        if c.get("pipe_or_mechanism_id") not in ids:
            err("UNLINKED_CONTRAST",i,"Target ID must be part of accepted graph")
        if c.get("type") not in {"difference","possible_difference","none"}:
            err("CONTRAST_TYPE_VALUE",i,"Invalid contrast type")
        if not str(c.get("explanation","")).strip():
            err("UNEXPLAINED_CONTRAST",i,"Explain observed/reference comparison")
        if c.get("type")=="none" and c.get("epistemic") in {"HIPÓTESIS","DESCONOCIDO"}:
            err("NONE_WITHOUT_PROOF",i,"Missing information cannot prove absence of deviation")
        refs=c.get("evidence_refs")
        if not isinstance(refs,list) or len(refs)<2:
            err("CONTRAST_REFERENCES",i,"Require public and calibrated reference sources")
            continue
        kinds=set()
        for ref in refs:
            if not isinstance(ref,dict):
                err("CONTRAST_REF_SCHEMA",i,"Invalid evidence ref")
                continue
            kind=source_map.get((ref.get("source_id"),ref.get("sha256")))
            if not kind:err("CONTRAST_UNKNOWN_SOURCE",i,"Unknown public evidence")
            kinds.add(kind)
        if not {"OBSERVADO","CALIBRADO"}.issubset(kinds):
            err("CONTRAST_REFERENCE_TYPES",i,"Must cite at least one observed and one calibrated source")
    if contrast.get("scenario_projections")!=[]:
        err("PROJECTION_NOT_ALLOWED","scenario_projections","Aggregate SD model is uncalibrated")
    decision=contrast.get("decision")
    if not isinstance(decision,dict) or decision.get("choice")!="abstain":
        err("PREMATURE_DECISION","decision","This experiment forbids uncalibrated decisions")
    actions=contrast.get("actions")
    if not isinstance(actions,list) or len(actions)!=3 or set(actions)!={"no_delivery","open_full","open_offpeak_capped"}:
        err("ACTIONS","actions","The exact three policies must be retained")
    ident=contrast.get("identifiability")
    if not isinstance(ident,dict) or ident.get("status") not in ("identifiable","non_identifiable","no_material_deviation","insufficient_data"):
        err("IDENTIFIABILITY_SCHEMA","identifiability","Valid status required")
    elif ident["status"]=="non_identifiable" and (
        len(ident.get("rival_mechanisms",[]))<2 or not str(ident.get("discriminating_measurement","")).strip()):
        err("RIVALS_REQUIRED","identifiability","Two mechanisms and separating measurement required")
    unknowns=contrast.get("unknowns")
    if not isinstance(unknowns,list) or not unknowns:
        err("UNKNOWN_REQUIRED","unknowns","Unknowns required while model is uncalibrated")
    # No mechanical repair or changes to accepted graph.
    combined={**graph,**{k:v for k,v in contrast.items() if k not in ("graph_sha256",)}}
    original=validate_model(combined,packet)
    semantic=audit_v2(combined,packet)
    if not original["accepted"]:
        for i in original["issues"]:
            err("BASE_"+i["code"],"combined",i["reason"])
    if not semantic["accepted"]:
        for i in semantic["issues"]:
            err("SEMANTIC_"+i["code"],i["where"],i["detail"])
    return {"accepted":not issues,"issues":issues,
            "graph_sha256":sha(graph),"contrast_count":len(cl),
            "base_validator":original,"semantic_v2":semantic,
            "validator":"IGC0_CONTRAST_GATE_V3"}
