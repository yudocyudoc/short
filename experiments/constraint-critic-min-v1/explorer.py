#!/usr/bin/env python3
"""IGC minimal constraint exploration: enumerator -> types -> OMC behavioral probes.

The semantic expectation is proposed by a LLM reviewer, NEVER certified by a
type checker. The verifier can test model behavior, but cannot prove that the
user's prose implies a proposed behavioral requirement. No raw LLM data enters
Modelica, no parameter values are sent to the reviewer.
"""
from __future__ import annotations
import csv,json,math
from pathlib import Path

HERE=Path(__file__).resolve().parent
POLICY_DIR=HERE.parent/"policy-choice-v1"
TEST_ID="NO_ACCEPTED_ORDERS"
ALLOWED={"STOPS","CONTINUES","UNKNOWN","CONFLICT"}

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def case_by_id(case_id):
    return next(c for c in read(HERE/"cases.json")["cases"] if c["id"]==case_id)

def enumerate_candidates():
    catalog=read(POLICY_DIR/"catalog.json")
    interfaces=catalog["interfaces"]
    start=interfaces["ORDER_SOURCE"]["ports"]["out"]
    end=interfaces["DELIVERY"]["ports"]["in"]
    candidates=[]
    for component in catalog["components"]:
        if component["kind"]!="ARCHITECTURE":
            continue
        name=component["id"]
        ports=interfaces[name]["ports"]
        if start!=ports.get("in") or ports.get("out")!=end:
            continue
        candidates.append({
            "id":name,
            "native_class":component["class"],
            "nodes":["ORDER_SOURCE",name,"DELIVERY"],
            "links":[["ORDER_SOURCE.out",name+".in"],[name+".out","DELIVERY.in"]],
            "structurally_valid":True,
            "meaning":component["purpose"],
            "exclusions":component.get("excludes",[])})
    return sorted(candidates,key=lambda x:x["id"])

def _rows(file):
    with Path(file).open(encoding="utf-8-sig",newline="") as f:
        values=[{k:float(v) for k,v in row.items()} for row in csv.DictReader(f)]
    if len(values)<2 or any(not math.isfinite(v) for r in values for v in r.values()):
        raise ValueError("MISSING_OR_INVALID_OPENMODELICA_SERIES")
    return values

def _field(row,name):
    if name in row:return row[name]
    matches=[v for k,v in row.items() if k.endswith("."+name)]
    if len(matches)!=1:raise ValueError("NO_UNIQUE_OMC_COLUMN:"+name)
    return matches[0]

def derive_actual_signatures(folder):
    """Require measured OMC series; never fill behavioral results by assumption."""
    mto=_rows(Path(folder)/"probe_no_orders_mto_res.csv")
    mts=_rows(Path(folder)/"probe_no_orders_mts_res.csv")
    eps=1e-6
    mto_stops=all(abs(_field(r,"preparationRate"))<eps
      and abs(_field(r,"dispatchRate"))<eps for r in mto)
    mts_produces=any(_field(r,"production")>eps for r in mts)
    if not mto_stops or not mts_produces:
        raise ValueError("UNEXPECTED_PROBE_SIGNATURE_CHECK_MODELS_AND_INPUT")
    return {"MTO":"STOPS","MTS":"CONTINUES"}

def validate_review(case,review):
    """Syntax, references and registered test only. NO semantic truth claim."""
    errors=[]
    keys={"case_id","test_id","expected","fact_ids","next_question"}
    if not isinstance(review,dict) or set(review)!=keys:
        return {"status":"INVALID","errors":["S_REVIEW_SCHEMA"]}
    if review["case_id"]!=case["id"]:errors.append("S_WRONG_CASE")
    if review["test_id"]!=TEST_ID:errors.append("T_UNKNOWN_COUNTERFACTUAL")
    if review["expected"] not in ALLOWED:errors.append("T_UNKNOWN_EXPECTATION")
    references=review["fact_ids"]
    available={x["id"] for x in case["facts"]}
    if not isinstance(references,list) or len(references)!=len(set(references)) or any(
         not isinstance(x,str) or x not in available for x in references):
        errors.append("E_UNKNOWN_FACT")
    if review["expected"] in {"STOPS","CONTINUES"} and (not references or len(references)<1):
        errors.append("E_NO_SUPPORT")
    if review["expected"]=="CONFLICT" and len(references)<2:
        errors.append("E_CONFLICT_NEEDS_TWO_FACTS")
    question=review["next_question"]
    if not isinstance(question,str) or len(question)>240:
        errors.append("S_QUESTION")
    if review["expected"] in {"UNKNOWN","CONFLICT"} and not question.strip():
        errors.append("E_NEED_DISCRIMINATING_QUESTION")
    return {"status":"VALID_REFERENCE_FORMAT" if not errors else "INVALID",
       "errors":errors,
       "semantic_entailment_verified":False}

def apply_review(candidates,signatures,review):
    """Only conditional pruning relative to reviewer's unverified prose reading."""
    expected=review["expected"]
    if expected in {"UNKNOWN","CONFLICT"}:
        kept=[c["id"] for c in candidates]
        rejected=[]
    else:
        kept=[c["id"] for c in candidates if signatures[c["id"]]==expected]
        rejected=[c["id"] for c in candidates if signatures[c["id"]]!=expected]
    return {
      "expected_behavior_proposed_by_reviewer":expected,
      "candidate_models":len(candidates),
      "kept":kept,
      "rejected":rejected,
      "requires_external_semantic_confirmation":True,
      "test_executed_in_openmodelica":TEST_ID,
      "test_observations":signatures,
      "discriminating_question":review["next_question"]}

def unification_only(candidates):
    return sorted(c["id"] for c in candidates)

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--probes",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    result={"experiment":"IGC_CONSTRAINT_CRITIC_MIN_V1",
      "architectures":enumerate_candidates(),
      "type_only_survivors":unification_only(enumerate_candidates()),
      "measured_signatures":derive_actual_signatures(args.probes)}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("DETERMINISTIC_ARCHITECTURE_EXPLORATION",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
