#!/usr/bin/env python3
"""EPI-04 adjudication. Deterministic oracle is sovereign; models are measured, never substituted."""
from __future__ import annotations
import argparse,json,math,re,statistics
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from oracle import ROOT,STATES,calculate_numeric,validate_all
from prepare import GOLD,dump,sha

FENCE=re.compile(r"^\s*" + chr(96)*3 + r"(?:json)?\s*\n(.*?)\n" + chr(96)*3 + r"\s*$",re.S|re.I)

def parse_glm(result):
    s=result.get("response")
    if not isinstance(s,str):
        choices=result.get("choices",[])
        if isinstance(choices,list) and choices:
            first=choices[0]
            s=first.get("message",{}).get("content") if isinstance(first.get("message"),dict) else first.get("text")
    if not isinstance(s,str):return None,["MISSING_TEXT"]
    flags=[]
    match=FENCE.fullmatch(s)
    if match:s=match.group(1);flags.append("FENCED_JSON")
    try:return json.loads(s),flags
    except json.JSONDecodeError:return None,flags+["INVALID_JSON"]

def decode_choice(result,model):
    issues=[]
    a=result.get("answers",{}).get("status") if model=="CLEF" else result
    if not isinstance(a,dict):return None,None,["MISSING_CHOICE_OBJECT"]
    chosen=a.get("choice")
    if chosen not in STATES:issues.append("INVALID_CHOICE")
    probs=a.get("probabilities")
    if not isinstance(probs,dict) or set(probs)!=set(STATES):
        return chosen,None,issues+["MISSING_PROBABILITIES"]
    if any(type(probs[k]) not in (float,int) or not math.isfinite(probs[k])
           or not 0<=probs[k]<=1 for k in STATES):
        return chosen,None,issues+["INVALID_PROBABILITY"]
    if abs(sum(probs.values())-1)>0.02:issues.append("NOT_NORMALIZED")
    if chosen in STATES and probs[chosen]+1e-6<max(probs.values()):
        issues.append("CHOICE_NOT_MAXIMUM")
    if issues:return chosen,None,issues
    return chosen,probs,[]

def brier(probs,truth):
    return sum((probs[k]-(k==truth))**2 for k in STATES)

def parse_clairic(result):
    a=result.get("answers",{}).get("calculated_value")
    if not isinstance(a,dict):return None,["MISSING_MATH_FIELD"]
    value=a.get("value")
    if type(value) not in (int,float) or not math.isfinite(value):
        return None,["NONNUMERIC_RESULT"]
    return Decimal(str(value)),[]

def mean(values):
    return round(statistics.mean(values),6) if values else None

def evaluate(out):
    validate_all()
    data=json.loads((out/"inference-manifest.json").read_text(encoding="utf-8"))
    gold=json.loads(GOLD.read_text(encoding="utf-8"))
    mathcases={x["id"]:x for x in json.loads((ROOT/"fixtures/math_cases.json").read_text(encoding="utf-8"))["cases"]}
    result={"schema":"short-epi04-evaluation/1","kind":"EXPLORATORY_PAIRED_CLASSIFICATION_AND_ARITHMETIC_CROSSCHECK",
      "source_manifest_sha256":sha((out/"inference-manifest.json").read_bytes()),
      "status":data["status"],"ground_truth":"deterministic exhaustive AND/OR + antichain parity; Decimal stock-flow conservation",
      "classification":[],"numeric_crosschecks":[],"by_model":{},"by_motif":{},"pairwise":{},
      "limitations":["20 cases in five correlated graph families; no frequentist generalization claim",
        "Probabilities refer to model confidence in logical category, not empirical hypothesis truth",
        "Clairic is an independent diagnostic: it cannot override the Decimal oracle"]}
    groups=defaultdict(list)
    bycase=defaultdict(dict)
    for record in data["runs"]:
        if record["status"]!="OK":continue
        raw=json.loads((out/("raw-"+record["prefix"]+".json")).read_text(encoding="utf-8"))
        if record["raw_sha256"]!=sha(dump(raw).encode()):
            raise AssertionError("Response artifact hash mismatch")
        response=raw.get("result",raw)
        if record["kind"]=="classification":
            parsed,flags=(parse_glm(response) if record["model"]=="GLM" else (response,[]))
            choice,probs,issues=decode_choice(parsed or {},record["model"])
            expected=gold["statuses"][record["id"]]
            row={"id":record["id"],"motif":record["motif"],"model":record["model"],
                 "gold":expected,"choice":choice,"correct":choice==expected and not issues,
                 "probabilities_valid":probs is not None,"brier":brier(probs,expected) if probs is not None else None,
                 "issues":issues,"format_flags":flags,"latency_ms":record.get("latency_ms"),
                 "usage":record.get("usage",{})}
            result["classification"].append(row)
            groups[record["model"]].append(row)
            bycase[record["id"]][record["model"]]=row
        else:
            value,issues=parse_clairic(response)
            reference=calculate_numeric(mathcases[record["id"]])
            if Decimal(str(gold["numerics"][record["id"]]))!=reference:
                raise AssertionError("Gold is inconsistent with Decimal arithmetic")
            equal=value==reference if value is not None else False
            row={"id":record["id"],"motif":record["motif"],
                 "oracle":str(reference),"clairic":str(value) if value is not None else None,
                 "verdict":"MATCH" if equal else ("DISAGREEMENT" if value is not None else "INVALID"),
                 "absolute_error":str(abs(value-reference)) if value is not None else None,
                 "math_ground_truth_retained":True,"issues":issues,
                 "latency_ms":record.get("latency_ms"),"usage":record.get("usage",{})}
            result["numeric_crosschecks"].append(row)
    for model in ("CLEF","GLM"):
        rows=groups.get(model,[])
        valid=[r["brier"] for r in rows if r["brier"] is not None]
        result["by_model"][model]={
            "n":len(rows),"correct":sum(r["correct"] for r in rows),
            "accuracy":sum(r["correct"] for r in rows)/len(rows) if rows else None,
            "brier_mean_on_valid_only":mean(valid),"brier_valid":len(valid),
            "brier_missing":len(rows)-len(valid),
            "latency_ms_mean":mean([r["latency_ms"] for r in rows if r["latency_ms"] is not None]),
            "usage_fields_sum":{k:sum(r["usage"].get(k,0) for r in rows if type(r["usage"].get(k)) in (int,float))
                       for k in ("prompt_tokens","completion_tokens","input_tokens","output_tokens","neurons")}
        }
        result["by_motif"][model]={motif:{
            "n":len(sub),"correct":sum(r["correct"] for r in sub)}
            for motif in sorted(set(r["motif"] for r in rows))
            for sub in [[r for r in rows if r["motif"]==motif]]}
    paired=[x for x in bycase.values() if "CLEF" in x and "GLM" in x]
    result["pairwise"]={"paired_cases":len(paired),
        "both_correct":sum(v["CLEF"]["correct"] and v["GLM"]["correct"] for v in paired),
        "clef_only_correct":sum(v["CLEF"]["correct"] and not v["GLM"]["correct"] for v in paired),
        "glm_only_correct":sum(v["GLM"]["correct"] and not v["CLEF"]["correct"] for v in paired),
        "both_wrong":sum(not v["CLEF"]["correct"] and not v["GLM"]["correct"] for v in paired)}
    numeric=result["numeric_crosschecks"]
    errors=[float(Decimal(x["absolute_error"])) for x in numeric if x["absolute_error"] is not None]
    result["math_crosscheck_summary"]={"n":len(numeric),"matches":sum(x["verdict"]=="MATCH" for x in numeric),
        "disagreements":sum(x["verdict"]=="DISAGREEMENT" for x in numeric),
        "invalid":sum(x["verdict"]=="INVALID" for x in numeric),
        "MAE_valid":mean(errors),"ground_truth_replaced":False}
    (out/"evaluation-report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--out",type=Path,default=ROOT/"results")
    result=evaluate(parser.parse_args().out)
    print(json.dumps({"status":result["status"],"by_model":result["by_model"],
        "pairwise":result["pairwise"],"math":result["math_crosscheck_summary"]},indent=2))
