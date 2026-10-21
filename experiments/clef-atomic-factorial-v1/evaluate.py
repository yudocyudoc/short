#!/usr/bin/env python3
"""EPI-06 2x2 factorial evaluation with independent logical gold.

Brier multiclass and Brier binary are incomparable; never pool them.
"""
from __future__ import annotations
import argparse,json,math,statistics
from pathlib import Path
from collections import defaultdict
from oracle import ROOT,STATES,validate
from prepare import CONDITIONS,encoded,sha

def decode(result,condition):
    answers=result.get("answers")
    if not isinstance(answers,dict):return None,None,["MISSING_ANSWERS"]
    if condition.startswith("BINARY"):
        marginals={}
        for h in ("h1_supported","h2_supported"):
            obj=answers.get(h)
            p=obj.get("noul") if isinstance(obj,dict) else None
            if type(p) not in (int,float) or not math.isfinite(p) or not 0<=p<=1:
                return None,None,["INVALID_NOUL:"+h]
            marginals[h]=float(p)
        h1=marginals["h1_supported"]>=.5
        h2=marginals["h2_supported"]>=.5
        label="BOTH" if h1 and h2 else "ONLY_H1" if h1 else "ONLY_H2" if h2 else "NEITHER"
        return label,marginals,[]
    obj=answers.get("status")
    if not isinstance(obj,dict):return None,None,["MISSING_CHOICE_ANSWER"]
    label=obj.get("choice")
    probabilities=obj.get("probabilities")
    problems=[]
    if label not in STATES:problems.append("INVALID_LABEL")
    if not isinstance(probabilities,dict) or set(probabilities)!=set(STATES):
        return None,None,problems+["INVALID_DISTRIBUTION_KEYS"]
    if any(type(probabilities[s]) not in (int,float) or not math.isfinite(probabilities[s]) or not 0<=probabilities[s]<=1 for s in STATES):
        return None,None,problems+["INVALID_DISTRIBUTION_RANGE"]
    if abs(sum(probabilities.values())-1)>.02:problems.append("NOT_NORMALIZED")
    if label in STATES and probabilities[label]+1e-6<max(probabilities.values()):
        problems.append("CHOICE_NOT_MAXIMUM")
    return label if not problems else None,probabilities if not problems else None,problems

def brier(prob,truth):
    if prob is None:return None
    if set(prob)==set(STATES):
        return sum((float(prob[s])-(1 if s==truth else 0))**2 for s in STATES)
    flags={"h1_supported":truth in ("BOTH","ONLY_H1"),"h2_supported":truth in ("BOTH","ONLY_H2")}
    return sum((prob[x]-(1 if flags[x] else 0))**2 for x in flags)/2

def aggregate(rows,condition):
    neither=[r for r in rows if r["gold"]=="NEITHER"]
    controls=[r for r in rows if r["gold"]!="NEITHER"]
    scores=[r["brier"] for r in rows if r["brier"] is not None]
    return {"n":len(rows),"n_correct":sum(r["correct"] for r in rows),
        "accuracy":sum(r["correct"] for r in rows)/len(rows) if rows else None,
        "neither_n":len(neither),"neither_false_support":sum(r["false_support"] for r in neither),
        "neither_correct":sum(r["correct"] for r in neither),
        "control_n":len(controls),"control_correct":sum(r["correct"] for r in controls),
        "invalid_responses":sum(bool(r["issues"]) for r in rows),
        "brier_type":"binary_mean" if condition.startswith("BINARY") else "multiclass",
        "brier_mean_valid_only":statistics.mean(scores) if scores else None,
        "brier_valid_n":len(scores),
        "mean_latency_ms":statistics.mean(r["latency_ms"] for r in rows) if rows else None}

def contrast(left,right,key="correct"):
    # The same case is paired across both conditions, no independent-sample assumption.
    common=sorted(set(left)&set(right))
    return {"paired_cases":len(common),
      "left_only":sum(bool(left[id][key]) and not right[id][key] for id in common),
      "right_only":sum(bool(right[id][key]) and not left[id][key] for id in common),
      "both_yes":sum(bool(left[id][key]) and bool(right[id][key]) for id in common),
      "both_no":sum(not left[id][key] and not right[id][key] for id in common)}

def evaluate(out):
    cases,gold=validate()
    manifest=json.loads((out/"inference-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") not in ("COMPLETE","INCOMPLETE_NO_RETRY"):
        raise AssertionError("Unexpected inference status")
    schedule=json.loads((out/"preparation-report.json").read_text(encoding="utf-8"))
    report={"schema":"short-epi06-evaluation/1","status":manifest["status"],
            "manifest_sha256":sha((out/"inference-manifest.json").read_bytes()),
            "fixture_sha256":schedule["fixture_sha256"],
            "primary_endpoint":"false support among 8 NEITHER cases",
            "secondary_endpoint":"accuracy among 12 controls, per-case paired changes",
            "probability_warning":"Four-class Brier and mean marginal binary Brier are incompatible scales",
            "interpretation":"exploratory two-by-two; repeated case correlations and single response per condition; instructional equivalence approximate",
            "records":[],"by_condition":{},"paired":{},"contrasts":{},"per_case":{}}
    bycondition=defaultdict(list)
    for item in manifest["records"]:
        if item["status"]!="OK":continue
        raw=json.loads((out/("raw-"+item["prefix"]+".json")).read_text(encoding="utf-8"))
        if sha(encoded(raw).encode())!=item["response_sha256"]:
            raise AssertionError("Tampered provider response: "+item["prefix"])
        output=raw.get("result",raw)
        chosen,probs,issues=decode(output,item["condition"])
        true=gold["case_class"][item["id"]]
        record={"id":item["id"],"condition":item["condition"],"gold":true,
            "choice":chosen,"correct":chosen==true and not issues,
            "false_support":true=="NEITHER" and chosen not in (None,"NEITHER"),
            "probabilities":probs,
            "brier":brier(probs,true),"brier_type":"binary_mean" if item["condition"].startswith("BINARY") else "multiclass",
            "confidence":(output.get("answers",{}).get("status",{}).get("confidence")
                          if item["condition"].startswith("CHOICE") else None),
            "issues":issues,"latency_ms":item.get("latency_ms"),"usage":item.get("usage",{})}
        report["records"].append(record)
        bycondition[item["condition"]].append(record)
    for cond in CONDITIONS:
        report["by_condition"][cond]=aggregate(bycondition[cond],cond)
    indexed={cond:{r["id"]:r for r in bycondition[cond]} for cond in CONDITIONS}
    comparisons={
       "task_effect_at_base":("CHOICE_BASE","BINARY_BASE"),
       "task_effect_at_explicit":("CHOICE_EXPLICIT","BINARY_EXPLICIT"),
       "instruction_effect_on_choice":("CHOICE_BASE","CHOICE_EXPLICIT"),
       "instruction_effect_on_binary":("BINARY_BASE","BINARY_EXPLICIT")}
    for name,(left,right) in comparisons.items():
        report["paired"][name]=contrast(indexed[left],indexed[right])
    # Change in aggregate ACCURACY, not probabilistic calibration nor causal inference.
    a={cond:report["by_condition"][cond]["accuracy"] for cond in CONDITIONS}
    if all(x is not None for x in a.values()):
        report["contrasts"]={
          "task_at_base_accuracy_delta":a["BINARY_BASE"]-a["CHOICE_BASE"],
          "task_at_explicit_accuracy_delta":a["BINARY_EXPLICIT"]-a["CHOICE_EXPLICIT"],
          "instruction_at_choice_accuracy_delta":a["CHOICE_EXPLICIT"]-a["CHOICE_BASE"],
          "instruction_at_binary_accuracy_delta":a["BINARY_EXPLICIT"]-a["BINARY_BASE"],
          "difference_in_differences_accuracy":(a["BINARY_EXPLICIT"]-a["CHOICE_EXPLICIT"])-(a["BINARY_BASE"]-a["CHOICE_BASE"])
        }
    for case in cases:
        report["per_case"][case["id"]]={"gold":gold["case_class"][case["id"]],
          "conditions":{c:{"choice":indexed[c][case["id"]]["choice"],
                           "correct":indexed[c][case["id"]]["correct"],
                           "probabilities":indexed[c][case["id"]]["probabilities"],
                           "issues":indexed[c][case["id"]]["issues"]}
                for c in CONDITIONS if case["id"] in indexed[c]}}
    (out/"evaluation-report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=ROOT/"results")
    report=evaluate(p.parse_args().out)
    print(json.dumps({"status":report["status"],"by_condition":report["by_condition"],
      "paired":report["paired"],"contrasts":report["contrasts"]},indent=2))
