#!/usr/bin/env python3
"""IGC-0 secondary semantic safeguards, distinct from original source validator.

This is a POSTHOC check built after the first M01 proposal exposed false acceptance.
It does not overwrite the frozen first-run verdict, substitute human causal review,
or infer model structure from the reference scaffold / evaluator's oracle.
"""
import argparse
import json
from pathlib import Path
from igc import all_evidence_refs

SUPPORTED={"OBSERVADO","CALIBRADO","INFERIDO","HIPÓTESIS","DESCONOCIDO","SIMULADO"}
SOURCE_REQUIRED={"OBSERVADO","CALIBRADO","INFERIDO"}
FAMILY_ALIASES={
  "meals_equivalent":"meal", "meal":"meal","meals":"meal","comidas":"meal",
  "orders":"order","order":"order","pedidos":"order",
  "mxn":"money","pesos":"money","money":"money",
  "requests":"request","request":"request"
}

def family(unit):
    if not isinstance(unit,str) or not unit.strip():
        return None
    raw=unit.lower().strip().split("/")[0].replace(" ","_")
    return FAMILY_ALIASES.get(raw,raw)

def audit(model,packet):
    issues=[]
    def add(code,where,detail):
        issues.append({"code":code,"where":where,"detail":detail})
    if not isinstance(model,dict):
        return {"accepted":False,"issues":[{"code":"SCHEMA","where":"root","detail":"Model must be object"}]}
    stocks=model.get("stocks",[])
    pipes=model.get("pipes",[])
    if not isinstance(stocks,list) or not isinstance(pipes,list):
        return {"accepted":False,"issues":[{"code":"SCHEMA","where":"root","detail":"stocks/pipes must be lists"}]}
    source_types=all_evidence_refs(packet)
    ids={}
    for s in stocks:
        if not isinstance(s,dict):continue
        sid=s.get("id")
        ids[sid]=s.get("unit")
        initial=s.get("initial")
        label=s.get("initial_label")
        refs=s.get("initial_refs",[])
        if isinstance(initial,(int,float)) and not isinstance(initial,bool):
            if label in SOURCE_REQUIRED and not refs:
                add("UNSUPPORTED_STOCK_INITIAL",sid,"Numeric initial has no evidence citation")
            if label=="DESCONOCIDO":
                add("UNJUSTIFIED_NUMERIC_INITIAL",sid,"Unknown initial was assigned a numeric value")
            if isinstance(refs,list) and label=="OBSERVADO":
                for x in refs:
                    if not isinstance(x,dict):continue
                    t=source_types.get((x.get("source_id"),x.get("sha256")))
                    if t and t!="OBSERVADO":
                        add("EPISTEMIC_MISMATCH",sid,"Initial source is "+str(t)+" but stock is labelled OBSERVADO")
    for p in pipes:
        if not isinstance(p,dict):continue
        pid=p.get("id","<missing>")
        src=p.get("from")
        dst=p.get("to")
        pf=family(p.get("unit_per_time"))
        if src in ids and dst in ids:
            af,bf=family(ids[src]),family(ids[dst])
            if af!=bf:
                add("CROSS_DOMAIN_STOCK_FLOW",pid,f"Cannot conserve {af} from stock '{src}' directly into {bf} stock '{dst}'")
            if pf not in (af,bf):
                add("RATE_STOCK_UNIT_MISMATCH",pid,"Flow unit incompatible with stock endpoints")
        elif src in ids or dst in ids:
            stock=src if src in ids else dst
            sf=family(ids[stock])
            if pf!=sf:
                add("RATE_STOCK_UNIT_MISMATCH",pid,f"Flow rate family {pf} incompatible with {sf} stock '{stock}'")
        label=p.get("epistemic")
        refs=p.get("evidence_refs",[])
        if label in SOURCE_REQUIRED and not refs:
            add("PIPE_WITHOUT_EVIDENCE",pid,"Asserted observed/calibrated/inferred pipe has no source citation")
        if label not in SUPPORTED:
            add("INVALID_PIPE_LABEL",pid,"Unrecognized epistemic label")
    contrasts=model.get("contrast")
    if not isinstance(contrasts,list) or not contrasts:
        add("MISSING_IGC_CONTRAST","contrast","IGC requires an explicit supported contrast or a sourced 'none' finding")
    else:
        for i,c in enumerate(contrasts):
            if not isinstance(c,dict):
                add("INVALID_CONTRAST",str(i),"Contrast must be object")
            elif c.get("epistemic") in SOURCE_REQUIRED and not c.get("evidence_refs"):
                add("CONTRAST_WITHOUT_EVIDENCE",str(i),"Contrast lacks traceable evidence")
    ident=model.get("identifiability")
    unknowns=model.get("unknowns")
    if not isinstance(unknowns,list):
        add("UNKNOWN_SCHEMA","unknowns","Expected list")
    if isinstance(ident,dict):
        status=ident.get("status")
        if status=="non_identifiable":
            if len(ident.get("rival_mechanisms",[]))<2 or not str(ident.get("discriminating_measurement","")).strip():
                add("NON_IDENTIFIABILITY_UNSUPPORTED","identifiability","Requires rival mechanisms and separating measurement")
        if status in ("insufficient_data","non_identifiable") and not unknowns:
            add("UNDECLARED_UNCERTAINTY","unknowns","Uncertain system should identify missing facts")
    return {"accepted":not issues,"issues":issues,
            "stock_count":len(stocks),"pipe_count":len(pipes),
            "contrast_count":len(contrasts) if isinstance(contrasts,list) else None,
            "checks":"source support; stock-flow dimensionality; explicit contrast; uncertainty",
            "status":"SECONDARY_POSTHOC_AUDIT"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model",type=Path,required=True)
    ap.add_argument("--packet",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    m=json.loads(a.model.read_text(encoding="utf-8"))
    p=json.loads(a.packet.read_text(encoding="utf-8"))
    x=audit(m,p)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(x,ensure_ascii=False))
if __name__=="__main__":
    main()
