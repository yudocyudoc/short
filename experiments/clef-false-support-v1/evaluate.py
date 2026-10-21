#!/usr/bin/env python3
"""EPI-05 strict audit and targeted factorial evaluation, no text generation."""
from __future__ import annotations
import argparse,json,math,statistics
from collections import defaultdict
from pathlib import Path
from oracle import ROOT,STATES,validate
from prepare import CONDITIONS,transport,sha

def evaluate_response(response,condition):
    answers=response.get("answers")
    if not isinstance(answers,dict):return None,None,["MISSING_ANSWERS"]
    if condition.endswith("BINARY"):
        probs=[]
        for key in ("h1_supported","h2_supported"):
            item=answers.get(key)
            value=item.get("noul") if isinstance(item,dict) else None
            if type(value) not in (float,int) or not math.isfinite(value) or not 0<=value<=1:
                return None,None,["INVALID_NOUL:"+key]
            probs.append(float(value))
        choice="BOTH" if probs[0]>=.5 and probs[1]>=.5 else "ONLY_H1" if probs[0]>=.5 else "ONLY_H2" if probs[1]>=.5 else "NEITHER"
        return choice,{"H1":probs[0],"H2":probs[1]},[]
    item=answers.get("status")
    if not isinstance(item,dict):return None,None,["MISSING_CHOICE"]
    choice=item.get("choice")
    prob=item.get("probabilities")
    errors=[]
    if choice not in STATES:errors.append("INVALID_OPTION")
    if not isinstance(prob,dict) or set(prob)!=set(STATES):
        return None,None,errors+["INVALID_PROBABILITY_KEYS"]
    if any(type(prob[k]) not in (float,int) or not math.isfinite(prob[k]) or not 0<=prob[k]<=1 for k in STATES):
        return None,None,errors+["INVALID_PROBABILITY"]
    if abs(sum(prob.values())-1)>.02:errors.append("NOT_NORMALIZED")
    if choice in STATES and prob[choice]+1e-6<max(prob.values()):errors.append("CHOICE_DISAGREES_WITH_MAXIMUM")
    return choice if not errors else None,prob if not errors else None,errors

def brier(choice,probs,expected):
    if probs is None:return None
    if set(probs)==set(STATES):
        return sum((probs[k]-(1 if k==expected else 0))**2 for k in STATES)
    # Different metric, for two separate support decisions. Never mix with multiclass Brier.
    truth={"H1":expected in ("BOTH","ONLY_H1"),"H2":expected in ("BOTH","ONLY_H2")}
    return sum((probs[k]-(1 if truth[k] else 0))**2 for k in ("H1","H2"))/2

def evaluate(out):
    cases,gold=validate()
    manifest=json.loads((out/"inference-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") not in ("COMPLETE","INCOMPLETE_NO_RETRY"):
        raise AssertionError("Unexpected run state")
    report={
       "schema":"short-epi05-evaluation/1","status":manifest["status"],
       "source_manifest_sha256":sha((out/"inference-manifest.json").read_bytes()),
       "gold_basis":"EPI-04 pre-existing gold confirmed by exhaustive and antichain oracles",
       "interpretation":"controlled exploratory ablation, not causal identification without repetitions",
       "records":[],"by_condition":{},"per_case":{},
       "no_inference_bias_warning":"Binary noul outputs are two marginal decisions; not a calibrated joint 4-category probability"}
    groups=defaultdict(list)
    for record in manifest.get("records",[]):
        if record["status"]!="OK":continue
        raw=json.loads((out/("raw-"+record["prefix"]+".json")).read_text(encoding="utf-8"))
        if sha(transport(raw).encode())!=record["response_sha256"]:
            raise AssertionError("Raw response differs from manifest: "+record["prefix"])
        result=raw.get("result",raw)
        predicted,probs,issues=evaluate_response(result,record["condition"])
        expected=gold["statuses"][record["id"]]
        row={"id":record["id"],"motif":record["source_motif"],"condition":record["condition"],
             "expected":expected,"predicted":predicted,"correct":predicted==expected and not issues,
             "false_support":expected=="NEITHER" and predicted not in (None,"NEITHER"),
             "probabilities":probs,"issues":issues,
             "brier_multiclass" if not record["condition"].endswith("BINARY") else "brier_binary_mean":
                  brier(predicted,probs,expected),
             "latency_ms":record.get("latency_ms"),"usage":record.get("usage",{})}
        groups[row["condition"]].append(row)
        report["records"].append(row)
    for condition in CONDITIONS:
        rows=groups[condition]
        neither=[r for r in rows if r["expected"]=="NEITHER"]
        other=[r for r in rows if r["expected"]!="NEITHER"]
        key="brier_binary_mean" if condition.endswith("BINARY") else "brier_multiclass"
        scores=[r[key] for r in rows if r[key] is not None]
        report["by_condition"][condition]={
             "n":len(rows),"correct":sum(r["correct"] for r in rows),
             "neither_n":len(neither),"false_support_count":sum(r["false_support"] for r in neither),
             "neither_correct":sum(r["correct"] for r in neither),
             "positive_controls_n":len(other),"positive_controls_correct":sum(r["correct"] for r in other),
             "format_or_range_issues":sum(bool(r["issues"]) for r in rows),
             key+"_mean_on_valid":statistics.mean(scores) if scores else None,
             "latency_ms_mean":statistics.mean([r["latency_ms"] for r in rows]) if rows else None}
    for case in cases:
        report["per_case"][case["id"]]={
            r["condition"]:{"predicted":r["predicted"],"correct":r["correct"],
                            "probabilities":r["probabilities"],"issues":r["issues"]}
            for r in report["records"] if r["id"]==case["id"]}
    (out/"evaluation-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=ROOT/"results")
    result=evaluate(p.parse_args().out)
    print(json.dumps({"status":result["status"],"by_condition":result["by_condition"]},ensure_ascii=False,indent=2))
