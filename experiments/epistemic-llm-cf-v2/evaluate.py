#!/usr/bin/env python3
"""Post-inference EPI-02 validation, fixed-gold scoring and blind review packets.
Never repairs a semantic statement or changes the model's original answer.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import re
from collections import defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
FENCE=re.compile(r"^\s*" + chr(96)*3 + r"(?:json)?\s*\n(.*?)\n" + chr(96)*3 + r"\s*$",re.I|re.S)

def parse(text):
    try:
        return json.loads(text),"PURE_JSON",[]
    except json.JSONDecodeError:
        m=FENCE.fullmatch(text)
        if not m:
            return None,"INVALID_JSON",["JSON_PARSE_FAILED"]
        try:
            return json.loads(m.group(1)),"FENCES_REMOVED",["NON_PURE_JSON_FENCES"]
        except json.JSONDecodeError:
            return None,"INVALID_JSON",["JSON_PARSE_FAILED"]

def validate_answer(answer,case,task,gold):
    issues=[]
    if not isinstance(answer,dict):
        return {"issues":["NOT_JSON_OBJECT"],"correct":0,"total":6 if task=="HISTORY" else 2}
    for field in ("case_id","task_id","hypothesis_states","justification_assessment","explanation","uncertainties"):
        if field not in answer:
            issues.append("MISSING_FIELD:"+field)
    if answer.get("case_id")!=case["id"]:
        issues.append("WRONG_CASE_ID")
    if answer.get("task_id")!=task:
        issues.append("WRONG_TASK_ID")
    revs=("R0","R1","R2") if task=="HISTORY" else ("CF",)
    expected={(rev,h):gold[rev][h] for rev in revs for h in gold[rev]}
    hypothesis_ids={h["id"] for h in case["hypotheses"]}
    record_ids={x["id"] for x in case["records"]}
    assumption_ids={x["id"] for x in case["assumptions"]}
    rules_by_id={x["id"]:x for x in case["rules"]}
    states=answer.get("hypothesis_states",[])
    seen=set()
    predictions={}
    if not isinstance(states,list):
        issues.append("STATES_NOT_ARRAY")
        states=[]
    for item in states:
        if not isinstance(item,dict):
            issues.append("INVALID_STATE_OBJECT")
            continue
        h=item.get("hypothesis_id")
        rev=item.get("revision")
        val=item.get("status")
        if not isinstance(h,str) or "|" in h or h not in hypothesis_ids:
            issues.append("INVALID_HYPOTHESIS_ID:"+str(h))
            continue
        if rev not in revs:
            issues.append("INVALID_REVISION:"+str(rev))
            continue
        if val not in ("SUPPORTED","UNSUPPORTED"):
            issues.append("INVALID_STATE_VALUE:"+str(val))
            continue
        slot=(rev,h)
        if slot in seen:
            issues.append("DUPLICATE_STATE:"+rev+":"+h)
            predictions.pop(slot,None)
            continue
        seen.add(slot)
        predictions[slot]=val
    for rev,h in sorted(set(expected)-seen):
        issues.append("MISSING_STATE:"+rev+":"+h)
    validations=answer.get("justification_assessment",[])
    if not isinstance(validations,list):
        issues.append("JUSTIFICATIONS_NOT_ARRAY")
        validations=[]
    seen_j=set()
    active_rules=set()
    for item in validations:
        if not isinstance(item,dict):
            issues.append("INVALID_JUSTIFICATION_OBJECT")
            continue
        rid=item.get("justification_id")
        if not isinstance(rid,str) or "|" in rid or rid not in rules_by_id:
            issues.append("INVALID_JUSTIFICATION_ID:"+str(rid))
        else:
            if rid in seen_j:
                issues.append("DUPLICATE_JUSTIFICATION:"+rid)
            seen_j.add(rid)
            if item.get("status")=="ACTIVE":
                active_rules.add(rid)
        if item.get("status") not in ("ACTIVE","INACTIVE","UNKNOWN"):
            issues.append("INVALID_JUSTIFICATION_STATUS:"+str(item.get("status")))
        for field,allowed in (("evidence_refs",record_ids),("assumption_refs",assumption_ids)):
            values=item.get(field)
            if not isinstance(values,list):
                issues.append("NOT_ARRAY:"+field)
                continue
            for value in values:
                if not isinstance(value,str) or "|" in value or value not in allowed:
                    issues.append("INVALID_REFERENCE:"+field+":"+str(value))
    target_rev="R2" if task=="HISTORY" else "CF"
    for rid in active_rules:
        target=rules_by_id[rid]["consequent"]
        if target in hypothesis_ids and predictions.get((target_rev,target))=="UNSUPPORTED":
            issues.append("INTERNAL_CONTRADICTION_ACTIVE_SUPPORT:"+rid)
    if not isinstance(answer.get("explanation"),str):
        issues.append("EXPLANATION_NOT_STRING")
    if not isinstance(answer.get("uncertainties"),list):
        issues.append("UNCERTAINTIES_NOT_ARRAY")
    correct=sum(predictions.get(slot)==truth for slot,truth in expected.items())
    return {"issues":sorted(set(issues)),"correct":correct,"total":len(expected),
            "state_accuracy":round(correct/len(expected),4),"present_states":len(predictions)}

def evaluate(results_dir):
    manifest=json.loads((results_dir/"inference-manifest.json").read_text(encoding="utf-8"))
    cases=json.loads((HERE/"cases.json").read_text(encoding="utf-8"))["cases"]
    gold=json.loads((HERE/"evaluation/gold.json").read_text(encoding="utf-8"))["cases"]
    by_case={x["id"]:x for x in cases}
    records=[]
    packets=[]
    totals=defaultdict(lambda:{"correct":0,"total":0,"count":0,"input_tokens":0,"output_tokens":0,"neurons":0})
    for item in manifest["runs"]:
        if item["status"]!="ok":
            continue
        raw=(results_dir/("answer-"+item["prefix"]+".txt")).read_text(encoding="utf-8")
        parsed,form,format_issues=parse(raw)
        grade=validate_answer(parsed,by_case[item["case"]],item["task"],gold[item["case"]])
        metrics=item.get("usage",{})
        row={**{k:item[k] for k in ("sequence","case","arm","task","rep")},"format":form,
             "format_issues":format_issues,**grade,"usage":metrics}
        records.append(row)
        group=totals[(item["arm"],item["task"])]
        group["correct"]+=grade["correct"]
        group["total"]+=grade["total"]
        group["count"]+=1
        group["input_tokens"]+=int(metrics.get("prompt_tokens") or 0)
        group["output_tokens"]+=int(metrics.get("completion_tokens") or 0)
        group["neurons"]+=float(metrics.get("neurons") or 0)
        packets.append({"sequence":item["sequence"],"case":item["case"],"task":item["task"],
                        "answer_original":raw})
    random.Random(20261022).shuffle(packets)
    blind=results_dir/"blinded"
    blind.mkdir(exist_ok=True)
    mapping={}
    for i,packet in enumerate(packets,1):
        alias=f"BLIND-{i:03d}"
        mapping[alias]=packet["sequence"]
        (blind/(alias+".json")).write_text(json.dumps({"case":packet["case"],"task":packet["task"],
                    "answer_original":packet["answer_original"]},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (results_dir/"blinding-map.json").write_text(json.dumps({"seed":20261022,"mapping":mapping},indent=2)+"\n",encoding="utf-8")
    summary={arm+"-"+task:dict(x) for (arm,task),x in sorted(totals.items())}
    report={"schema":"short-epi02-evaluation/1.0","evaluation_kind":"DETERMINISTIC_PREREGISTERED_STATES_ONLY",
            "source_manifest_sha256":hashlib.sha256((results_dir/"inference-manifest.json").read_bytes()).hexdigest(),
            "inference_status":manifest["status"],"scoring":"one point per hypothesis per revision; no post-hoc reweighting",
            "posthoc_human_review":"NOT_PERFORMED","records":records,"by_arm_and_task":summary,
            "blind_files_created":len(packets),"blinding_map_kept_outside_blinded_directory":True,
            "claims_of_general_superiority":False}
    (results_dir/"evaluation-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--results",type=Path,required=True)
    args=ap.parse_args()
    report=evaluate(args.results)
    print(json.dumps({k:report[k] for k in ("inference_status","by_arm_and_task","blind_files_created")},ensure_ascii=False,indent=2))
