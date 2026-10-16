#!/usr/bin/env python3
"""Fail-closed, evidence-grounded architecture/policy compiler for IGC v1.

The model selects documented mechanisms and cites fact IDs. Numeric simulation
is delegated ONLY to pre-existing validated synthetic fixtures and never
constructed from invented parameters or model-supplied code.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

HERE=Path(__file__).resolve().parent
FIELDS=("MODELO","POLITICAS","COMPONENTES","EVIDENCIAS","ACCION","FALTANTES")
VALID_MODELS={"MTO","MTS","INDETERMINADO"}
VALID_ACTIONS={"SIMULAR_CONDICIONAL","SOLO_ESTRUCTURA","ABSTENER"}

def read(name):
    return json.loads((HERE/name).read_text(encoding="utf-8"))

def case_map():
    return {c["id"]:c for c in read("cases_public.json")["cases"]}

def list_tokens(s):
    if s.strip().upper() in {"NINGUNA","NINGUNO","NINGUNOS",""}:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]

def parse(text):
    if not isinstance(text,str) or not 1<=len(text)<=12000:
        raise ValueError("INVALID_LENGTH")
    found={}
    for line in text.replace("\r\n","\n").split("\n"):
        if not line.strip():continue
        key,colon,value=line.partition(":")
        key=key.strip().upper()
        if colon!=":" or key not in FIELDS:
            raise ValueError("EXTRA_TEXT_OR_UNKNOWN_FIELD")
        if key in found:
            raise ValueError("DUPLICATE_FIELD:"+key)
        found[key]=value.strip()
    if set(found)!=set(FIELDS):
        raise ValueError("MISSING_FIELDS:"+",".join(sorted(set(FIELDS)-set(found))))
    if found["MODELO"] not in VALID_MODELS:
        raise ValueError("UNKNOWN_MODEL")
    if found["ACCION"] not in VALID_ACTIONS:
        raise ValueError("UNKNOWN_ACTION")
    for key in ("POLITICAS","COMPONENTES","EVIDENCIAS"):
        vals=list_tokens(found[key])
        if len(vals)!=len(set(vals)):
            raise ValueError("DUPLICATE_TOKEN:"+key)
        found[key]=vals
    if not found["FALTANTES"] or (found["ACCION"]!="SIMULAR_CONDICIONAL" and
                                  found["FALTANTES"].upper() in {"NINGUNO","NINGUNA","NO","NADA"}):
        raise ValueError("MISSING_DECLARED_UNCERTAINTY")
    if re.search(r"[<>]|\x60\x60\x60|;\s*(?:import|exec|loadModel|system)\b",text,re.I):
        raise ValueError("EXECUTABLE_OR_MARKUP_NOT_ALLOWED")
    return found

def factual_support(case_id,refs):
    facts=read("contracts.json")["fact_tags"][case_id]
    tags_all={tag for items in facts.values() for tag in items}
    tags_cited={tag for ref in refs for tag in facts[ref]}
    return tags_all,tags_cited

def supported_model(tags):
    catalog=read("catalog.json")["architectures"]
    for a,b in read("contracts.json")["conflict_tags"]:
        if a in tags and b in tags:
            return "INDETERMINADO","CONTRADICTORY_EVIDENCE"
    valid=[kind for kind,cfg in catalog.items()
           if set(cfg["required_tags"]).issubset(tags)]
    if len(valid)==1:return valid[0],"SUFFICIENT_STRUCTURAL_EVIDENCE"
    if len(valid)>1:return "INDETERMINADO","MULTIPLE_SUPPORTED_STRUCTURES"
    return "INDETERMINADO","INSUFFICIENT_STRUCTURAL_EVIDENCE"

def reject(case_id,reason,details=None):
    return {"case_id":case_id,"status":"REJECTED","reason":reason,
            "safe_to_simulate":False,"handoff":None,
            "details":details or {}}

def compile_proposal(case_id,response):
    cases=case_map()
    if case_id not in cases:raise KeyError("UNKNOWN_CASE:"+case_id)
    try:
        p=parse(response)
    except ValueError as exc:
        return reject(case_id,"FORMAT:"+str(exc))
    ids={item["id"] for item in cases[case_id]["facts"]}
    refs=p["EVIDENCIAS"]
    if not refs or set(refs)-ids:
        return reject(case_id,"UNKNOWN_OR_MISSING_EVIDENCE_CITATIONS")
    all_tags,cited_tags=factual_support(case_id,refs)
    model,why=supported_model(all_tags)
    selected=p["MODELO"]
    if selected!=model:
        return reject(case_id,"UNSUPPORTED_OR_CONTRADICTED_ARCHITECTURE",
                      {"proposed":selected,"supported":model,"evidence_reason":why})
    if model=="INDETERMINADO":
        if p["ACCION"]!="ABSTENER" or p["POLITICAS"] or p["COMPONENTES"]:
            return reject(case_id,"INDETERMINATE_MUST_ABSTAIN_WITHOUT_COMPONENTS")
        return {"case_id":case_id,"status":"VALID_ABSTENTION","reason":why,
                "safe_to_simulate":False,"handoff":None,
                "grounded_in":refs,"missing_data":p["FALTANTES"]}
    cfg=read("catalog.json")["architectures"][model]
    if not set(cfg["required_tags"]).issubset(cited_tags):
        return reject(case_id,"MISSING_CITATIONS_FOR_CAUSAL_STRUCTURE",
                      {"required_facts":cfg["required_tags"]})
    if set(p["POLITICAS"])!=set(cfg["policies"]):
        return reject(case_id,"UNAUTHORIZED_OR_INCOMPLETE_POLICIES")
    if set(p["COMPONENTES"])!=set(cfg["blocks"]):
        return reject(case_id,"UNAUTHORIZED_OR_INCOMPLETE_COMPONENTS")
    if p["ACCION"]=="ABSTENER":
        return {"case_id":case_id,"status":"VALID_CONSERVATIVE_ABSTENTION",
                "safe_to_simulate":False,"handoff":None,"grounded_in":refs,
                "reason":"LLM_ABSTAINED_WITH_SUPPORTED_STRUCTURE",
                "missing_data":p["FALTANTES"]}
    fixture=cfg["numeric_fixture"]
    fixture_evidenced="fixture:"+fixture in cited_tags
    if p["ACCION"]=="SIMULAR_CONDICIONAL" and not fixture_evidenced:
        return reject(case_id,"SIMULATION_REQUIRES_VERIFIED_COMPLETE_SYNTHETIC_FIXTURE",
                      {"model":model,"offered_fixture":fixture,
                       "independent_numeric_gate":False})
    status=("READY_FOR_EXISTING_SYNTHETIC_RUNNER" if p["ACCION"]=="SIMULAR_CONDICIONAL"
            else "STRUCTURE_ONLY_NO_SIMULATION")
    handoff=({"fixture":fixture,"existing_experiment":cfg["existing_experiment"],
              "conditions":"synthetic_only; external runner must recheck fixed inputs"}
             if status=="READY_FOR_EXISTING_SYNTHETIC_RUNNER" else None)
    return {"case_id":case_id,"status":status,"reason":"ACCEPTED_BY_INDEPENDENT_CHECKS",
            "selected_architecture":model,"selected_policies":cfg["policies"],
            "selected_components":cfg["blocks"],"grounded_in":refs,
            "missing_data":p["FALTANTES"],"safe_to_simulate":handoff is not None,
            "handoff":handoff,"source_claim":"SELECTION_PROPOSAL_NOT_MODEL_VALIDATION"}

def score_run(proposals):
    expected=read("answer_key.json")["cases"]
    results=[]
    for case_id,goal in expected.items():
        raw=proposals.get(case_id)
        if not isinstance(raw,str):
            out=reject(case_id,"NO_ACTUAL_MODEL_RESPONSE")
            results.append({"case_id":case_id,"evaluated":False,"correct":False,
                            "guardrail_safe":True,"compiler":out,"target":goal})
            continue
        out=compile_proposal(case_id,raw)
        try:
            decision=parse(raw)
            chosen={"model":decision["MODELO"],"action":decision["ACCION"]}
        except ValueError:
            chosen=None
        is_valid=out["status"]!="REJECTED"
        correct=is_valid and chosen=={"model":goal["model"],"action":goal["action"]}
        correct=bool(correct and (out["handoff"] or {}).get("fixture")==goal["fixture"])
        unsafe=out["safe_to_simulate"] and not (goal["fixture"] and correct)
        results.append({"case_id":case_id,"evaluated":True,"correct":correct,
                        "guardrail_safe":not unsafe,"compiler":out,"target":goal,
                        "proposed":chosen})
    attempted=sum(r["evaluated"] for r in results)
    correct=sum(r["correct"] for r in results)
    unsafe=sum(not r["guardrail_safe"] for r in results)
    return {"experiment":"IGC_FIELD_SELECTION_V1","kind":"REAL_LLM_ONLY_WHEN_PROVIDED",
            "evaluated":attempted,"total":len(results),"correct":correct,
            "unsupported_simulations_passed":unsafe,
            "full_benchmark_pass":attempted==len(results) and correct==len(results) and unsafe==0,
            "cases":results}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--case",choices=sorted(case_map()))
    p.add_argument("--proposal",type=Path)
    p.add_argument("--proposals-json",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if bool(a.case)!=bool(a.proposal):p.error("both --case and --proposal required")
    if bool(a.case)==bool(a.proposals_json):p.error("select either one proposal or a proposal set")
    if a.case:
        answer=compile_proposal(a.case,a.proposal.read_text(encoding="utf-8"))
    else:
        answer=score_run(json.loads(a.proposals_json.read_text(encoding="utf-8")))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(answer,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("IGC_STRUCTURE_GATE",json.dumps(
        {"status":answer.get("status"),"full_benchmark_pass":answer.get("full_benchmark_pass"),
         "evaluated":answer.get("evaluated"),"correct":answer.get("correct")},
        ensure_ascii=False),flush=True)

if __name__=="__main__":main()
