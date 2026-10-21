#!/usr/bin/env python3
"""Post-run scoring on pre-frozen gold. Never changes, repairs, or normalizes probabilities."""
from __future__ import annotations
import argparse,json,math,re,statistics
from collections import defaultdict
from pathlib import Path
from prepare import HERE,OPTIONS,GOLD,dump,sha

FENCE=re.compile(r"^\s*" + chr(96)*3 + r"(?:json)?\s*\n(.*?)\n" + chr(96)*3 + r"\s*$",re.S|re.I)
def parse_glm(result):
    s=result.get("response")
    if not isinstance(s,str):
        choices=result.get("choices")
        if isinstance(choices,list) and choices:
            first=choices[0]
            s=first.get("message",{}).get("content") if isinstance(first.get("message"),dict) else first.get("text")
    if not isinstance(s,str):
        return None,["NO_GENERATED_TEXT"]
    flags=[]
    match=FENCE.fullmatch(s)
    if match:
        s=match.group(1)
        flags.append("FENCED_JSON")
    try:
        return json.loads(s),flags
    except (json.JSONDecodeError,TypeError):
        return None,flags+["INVALID_JSON"]

def valid_distribution(answer,model):
    errors=[]
    if not isinstance(answer,dict):
        return None,None,["NO_ANSWER"]
    if model=="CLEF":
        answer=answer.get("answers",{}).get("support_state")
    if not isinstance(answer,dict):
        return None,None,["MISSING_SUPPORT_STATE"]
    name=answer.get("choice")
    probs=answer.get("probabilities")
    if name not in OPTIONS:
        errors.append("INVALID_CHOICE")
    if not isinstance(probs,dict) or set(probs)!=set(OPTIONS):
        errors.append("INVALID_PROBABILITY_KEYS")
        return name,None,errors
    if any(isinstance(probs[k],bool) or not isinstance(probs[k],(float,int))
           or not math.isfinite(probs[k]) or not 0<=probs[k]<=1 for k in OPTIONS):
        return name,None,errors+["INVALID_PROBABILITY_VALUE"]
    s=sum(probs.values())
    if abs(s-1)>0.02:
        errors.append("PROBABILITIES_NOT_NORMALIZED")
    if name in OPTIONS and probs[name]+1e-6<max(probs.values()):
        errors.append("CHOICE_DISAGREES_WITH_MAX")
    # Fail closed: no silent renormalization.
    if errors:
        return name,None,errors
    return name,probs,[]

def brier(probs,truth):
    return sum((probs[k]-(1 if k==truth else 0))**2 for k in OPTIONS)

def numeric_value(result):
    answers=result.get("answers",{})
    entry=answers.get("stock_value") if isinstance(answers,dict) else None
    if not isinstance(entry,dict):
        return None,None,["MISSING_STOCK_VALUE"]
    value=entry.get("value")
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        return None,None,["INVALID_NUMERIC_VALUE"]
    lo,hi=entry.get("p10"),entry.get("p90")
    interval=None
    if isinstance(lo,(int,float)) and not isinstance(lo,bool) and isinstance(hi,(int,float)) and not isinstance(hi,bool) and math.isfinite(lo) and math.isfinite(hi) and lo<=hi:
        interval=[lo,hi]
    elif lo is not None or hi is not None:
        return value,None,["INVALID_INTERVAL"]
    return value,interval,[]

def evaluate(out):
    gold=json.loads(GOLD.read_text(encoding="utf-8"))
    manifest=json.loads((out/"inference-manifest.json").read_text(encoding="utf-8"))
    report={"schema":"short-epi03-evaluation/1","source_manifest_sha256":sha((out/"inference-manifest.json").read_bytes()),
            "status":manifest["status"],"classification":[],"numerics":[],
            "comparison":"Model probabilities over mutually exclusive LOGICAL STATUS labels, NOT posterior probabilities of empirical hypotheses",
            "evaluation_kind":"PREREGISTERED_EXPLORATORY","metrics":{}}
    groups=defaultdict(list)
    for rec in manifest["records"]:
        if rec["status"]!="OK":
            continue
        rpath=out/f"raw-{rec['prefix']}.json"
        raw=json.loads(rpath.read_text(encoding="utf-8"))
        result=raw.get("result",raw)
        if rec["type"]=="CLASSIFICATION":
            parsed,flags=(parse_glm(result) if rec["model"]=="GLM" else (result,[]))
            choice,probs,issues=valid_distribution(parsed,rec["model"])
            expected=gold["classification"][rec["id"]]
            row={"id":rec["id"],"model":rec["model"],"stratum":rec["stratum"],
                 "choice":choice,"gold":expected,"correct":choice==expected and not issues,
                 "valid_distribution":probs is not None,"brier":brier(probs,expected) if probs is not None else None,
                 "format_flags":flags,"issues":issues,"latency_ms":rec.get("latency_ms"),
                 "usage":rec.get("usage",{})}
            report["classification"].append(row)
            groups[(rec["stratum"],rec["model"])].append(row)
        else:
            val,interval,issues=numeric_value(result)
            goldvalue=gold["numerics"][rec["id"]]
            row={"id":rec["id"],"kind":rec["stratum"],"gold":goldvalue,"value":val,
                 "absolute_error":abs(val-goldvalue) if val is not None else None,
                 "interval":interval,"interval_contains_gold":interval[0]<=goldvalue<=interval[1] if interval else None,
                 "issues":issues,"latency_ms":rec.get("latency_ms"),"usage":rec.get("usage",{})}
            report["numerics"].append(row)
            groups[(rec["stratum"],"CLAIRIC")].append(row)
    for key,rows in sorted(groups.items()):
        stratum,model=key
        base={"n":len(rows),"latency_ms_mean":round(statistics.mean(x["latency_ms"] for x in rows if x["latency_ms"] is not None),2) if rows else None,
              "usage_raw_sum":{}}
        for row in rows:
            for field,value in row["usage"].items():
                if type(value) in (int,float):
                    base["usage_raw_sum"][field]=base["usage_raw_sum"].get(field,0)+value
        if model!="CLAIRIC":
            good=[r["brier"] for r in rows if r["brier"] is not None]
            base.update({"correct":sum(r["correct"] for r in rows),
                "accuracy":sum(r["correct"] for r in rows)/len(rows) if rows else None,
                "valid_probabilities":len(good),"brier_mean_on_valid_only":statistics.mean(good) if good else None,
                "brier_missing_or_invalid":len(rows)-len(good)})
        else:
            errs=[r["absolute_error"] for r in rows if r["absolute_error"] is not None]
            base.update({"MAE_on_valid_only":statistics.mean(errs) if errs else None,
                        "valid_values":len(errs),"exact_count":sum(x==0 for x in errs),
                        "interval_available":sum(r["interval"] is not None for r in rows),
                        "interval_covered":sum(r["interval_contains_gold"] is True for r in rows)})
        report["metrics"][stratum+"/"+model]=base
    path=out/"evaluation-report.json"
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,default=HERE/"results")
    r=evaluate(ap.parse_args().out)
    print(json.dumps({"status":r["status"],"metrics":r["metrics"]},ensure_ascii=False,indent=2))
