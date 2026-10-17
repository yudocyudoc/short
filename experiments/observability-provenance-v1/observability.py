#!/usr/bin/env python3
"""IGC observation guard: synthetic telemetry may prune; prose alone may not.

This experiment deliberately does NOT infer temporal lag from max|x-y|.
Non-equality of sampled rates is reported as DISTINCT, not LAG.
Only correctly typed, measured-in-the-synthetic-world contrasts are hard
constraints. Everything here is SIMULATED, never organizational OBSERVADO.
"""
from __future__ import annotations
import argparse, json, math, os, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
DUAL=HERE.parent/"dual-mechanism-v1"
sys.path.insert(0,str(DUAL))
from analyze import rows, col, TESTS, NAMES  # existing OpenModelica CSV reader
import critic as old_critic

PAIRS={
 "OBSERVED_VS_DISPATCH":("dispatchRate","reportedDeliveryRate"),
 "PHYSICAL_VS_DISPATCH":("dispatchRate","deliveryRate"),
 "OBSERVED_VS_PHYSICAL":("deliveryRate","reportedDeliveryRate"),
}
SIGNALS={
 "dispatchRate":{"source_id":"dispatch_log","source_type":"ERP_EXPORT","unit":"orders/time_unit","cost":1},
 "deliveryRate":{"source_id":"receipt_scan","source_type":"RECEIVER_SCAN","unit":"orders/time_unit","cost":3},
 "reportedDeliveryRate":{"source_id":"dashboard","source_type":"DASHBOARD","unit":"orders/time_unit","cost":1},
}
STATUS=("SYNC","DISTINCT","UNKNOWN")
ALL=set(NAMES)
TOL=1e-6

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def save(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def validate_manifest(cases,truth):
    ids=set()
    for case in cases:
        cid=case["id"]
        if cid in ids or cid not in truth:raise ValueError("BAD_CASE_ID:"+cid)
        ids.add(cid)
        if truth[cid] not in ALL:raise ValueError("BAD_HIDDEN_TRUTH:"+cid)
        visible=case["available_signals"]
        if len(visible)!=len(set(visible)) or set(visible)-set(SIGNALS):
            raise ValueError("BAD_SIGNAL_MASK:"+cid)
        if set(case.get("unit_overrides",{}))-set(visible):raise ValueError("UNIT_OVERRIDE_NOT_VISIBLE")
        if not isinstance(case.get("claims",[]),list):raise ValueError("BAD_DOCUMENTS")
    if ids!=set(truth):raise ValueError("CASE_TRUTH_SET_MISMATCH")

def simulate_measurements(case,source):
    """Rates all come from SAME OpenModelica time grid, not invented curves."""
    if len(source)<10 or "time" not in source[0]:
        raise ValueError("NO_TIME_GRID")
    ts=[r["time"] for r in source]
    if any(not math.isfinite(t) for t in ts) or any(b<=a for a,b in zip(ts,ts[1:])):
        raise ValueError("BAD_TIME_GRID")
    output={}
    for name in case["available_signals"]:
        meta={**SIGNALS[name],"unit":case.get("unit_overrides",{}).get(name,SIGNALS[name]["unit"])}
        vals=[col(r,name) for r in source]
        if len(vals)!=len(ts) or any(not math.isfinite(v) for v in vals):
            raise ValueError("BAD_RATE_SERIES:"+name)
        output[name]={**meta,"status":"AVAILABLE","provenance":"SIMULADO",
            "time_grid_id":"OM_PULSE_0_8_64","n":len(ts),"values":vals}
    return output

def contrast(left,right):
    if left["unit"]!=right["unit"]:
        return "UNKNOWN","INCOMPATIBLE_UNITS"
    if left["source_id"]==right["source_id"]:
        return "UNKNOWN","NONINDEPENDENT_CHANNELS"
    if left["time_grid_id"]!=right["time_grid_id"] or left["n"]!=right["n"]:
        return "UNKNOWN","INCOMPATIBLE_TIME_GRID"
    difference=max(abs(x-y) for x,y in zip(left["values"],right["values"]))
    return ("SYNC" if difference<=TOL else "DISTINCT"),difference

def measurements(case,source):
    recorded=simulate_measurements(case,source)
    tests={};diagnostics={}
    for test,(a,b) in PAIRS.items():
        if a not in recorded or b not in recorded:
            tests[test]="UNKNOWN"
            diagnostics[test]={"reason":"SIGNAL_NOT_RECORDED",
                "needed":[x for x in (a,b) if x not in recorded]}
        else:
            status,detail=contrast(recorded[a],recorded[b])
            tests[test]=status
            diagnostics[test]={"reason":"NUMERIC_DIFFERENCE_NOT_TEMPORAL_LAG" if status=="DISTINCT"
                 else "COMPARISON", "max_abs_rate_difference":detail if isinstance(detail,float) else None,
                 "obstacle":detail if isinstance(detail,str) else None,
                 "source_ids":[recorded[a]["source_id"],recorded[b]["source_id"]]}
    return tests,diagnostics

def convert_signatures(probes):
    if probes.get("status")!="PASS" or not probes.get("all_four_joint_signatures_distinct"):
        raise ValueError("UNVERIFIED_OPENMODELICA_PROBES")
    sig=probes["signatures"]
    if set(sig)!=set(PAIRS):raise ValueError("MISSING_TESTS")
    result={}
    for test,architectures in sig.items():
        if set(architectures)!=ALL:raise ValueError("MISSING_GRAPHS")
        result[test]={}
        for name,value in architectures.items():
            if value not in ("SYNC","LAG"):raise ValueError("UNKNOWN_PRIOR_SIGNATURE")
            result[test][name]="SYNC" if value=="SYNC" else "DISTINCT"
    return result

def compatible(sig,tests):
    observed={t:v for t,v in tests.items() if v!="UNKNOWN"}
    return sorted(n for n in ALL if all(sig[t][n]==value for t,value in observed.items()))

def select_measurement(sig,remaining,tests,case):
    """Cost-aware partition suggestion; never claims the data already exist."""
    if len(remaining)<2:return None
    choices=[]
    possible=set(case.get("obtainable_signals",SIGNALS))
    for test,(a,b) in PAIRS.items():
        if tests[test]!="UNKNOWN":continue
        groups={sig[test][n] for n in remaining}
        if len(groups)<2:continue
        needed=set((a,b))-set(case["available_signals"])
        # If an available signal is invalid due to units, its repair still costs.
        invalid=set(case.get("unit_overrides",{})) & set((a,b))
        needed|=invalid
        if not needed or not needed<=possible:continue
        cost=sum(SIGNALS[x]["cost"] for x in needed)
        if cost>case.get("measurement_budget",3):continue
        counts={val:sum(sig[test][n]==val for n in remaining) for val in groups}
        n=len(remaining);gini=1-sum((c/n)**2 for c in counts.values())
        choices.append((-gini/cost,cost,test,sorted(needed),gini))
    if not choices:return None
    _,cost,test,needed,gini=min(choices)
    return {"test":test,"instrument_or_repair":needed,"relative_cost":cost,
            "partition_gini":gini,"status":"PROPOSED_NOT_OBSERVED",
            "requires_real_world_feasibility_check":True}

def evaluate_case(case,truth,series_folder,sig):
    data=rows(Path(series_folder)/("pulse_"+truth+"_res.csv"))
    statuses,detail=measurements(case,data)
    kept=compatible(sig,statuses)
    if truth not in kept:
        raise AssertionError("FALSE_ELIMINATION_BY_TELEMETRY:"+case["id"])
    return {"case_id":case["id"],"provenance":"SIMULADO_NOT_REAL_COMPANY",
        "known_contrasts":statuses,"diagnostics":detail,
        "available_signals":case["available_signals"],
        "survivors_measured_only":kept,
        "false_elimination":truth not in kept,
        "next_measurement":select_measurement(sig,kept,statuses,case),
        "document_claims_not_used_as_hard_constraints":True,
        "temporal_lag_inference":"NOT_ATTEMPTED"}

def critic_case(case,item):
    """Same evidence for baseline Llama and guarded evaluation; never show truth."""
    facts=[{"id":c["id"],"text":c["text"],"kind":"UNVERIFIED_DOCUMENT"} for c in case.get("claims",[])]
    for name in SIGNALS:
        facts.append({"id":"AV_"+name,"kind":"SYNTHETIC_TELEMETRY_METADATA",
           "text":(name+" available in a synthetic telemetry export" if name in case["available_signals"]
                else name+" NOT measured in this case")})
    for test,value in item["known_contrasts"].items():
        if value!="UNKNOWN":
            facts.append({"id":"OBS_"+test,"kind":"SIMULATED_COMPARISON",
             "text":test+" = "+value+" from numerical comparison of available synthetic rate series. "+
                "DISTINCT means not numerically equal, not proof of temporal lag."})
    return {"id":case["id"],"title":case["title"],"facts":facts}

def summarize(cases,results):
    assert len(cases)==len(results)
    return {"cases":len(results),
            "false_eliminations":sum(r["false_elimination"] for r in results),
            "singletons":sum(len(r["survivors_measured_only"])==1 for r in results),
            "abstentions_multiple_models":sum(len(r["survivors_measured_only"])>1 for r in results),
            "suggested_measurements":sum(r["next_measurement"] is not None for r in results),
            "mean_models_remaining":sum(len(r["survivors_measured_only"]) for r in results)/len(results),
            "method":"deterministic telemetry only, not LLM and not real organizational data"}

def run(series_folder,probe_file,out,call_llama=False):
    cases=read(HERE/"cases.json")["cases"]
    truth=read(HERE/"truth.json")["truth"]
    validate_manifest(cases,truth)
    sig=convert_signatures(read(probe_file))
    results=[evaluate_case(c,truth[c["id"]],series_folder,sig) for c in cases]
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    save(out/"measurement_results.json",results)
    save(out/"measurement_score.json",summarize(cases,results))
    promptset=[{"case_id":c["id"],"case":critic_case(c,r),
                "known_contrasts":r["known_contrasts"],"candidate_signatures":sig}
               for c,r in zip(cases,results)]
    save(out/"critic_inputs_no_truth.json",promptset)
    if not call_llama:
        save(out/"llama_status.json",{"status":"NOT_RUN","reason":"use --llama with existing Cloudflare secrets"})
        return summarize(cases,results)
    account=os.environ.get("CLOUDFLARE_ACCOUNT_ID","")
    token=os.environ.get("CLOUDFLARE_API_TOKEN","")
    if not account or not token:raise ValueError("MISSING_CLOUDFLARE_CREDENTIALS")
    baseline=[];rawdir=out/"llama_original"
    rawdir.mkdir(exist_ok=True)
    for c,r in zip(cases,results):
        payload=critic_case(c,r)
        msgs=old_critic.messages(payload,{
          t:{n:("LAG" if v=="DISTINCT" else v) for n,v in dic.items()}
          for t,dic in sig.items()})
        # Both arms see the SAME synthetic measurement results and source metadata.
        msgs[-1]["content"]+=("\nSYNTHETIC_MEASURED_TESTS: "+
                json.dumps(r["known_contrasts"],ensure_ascii=False)+
                "\nA numeric DISTINCT does not by itself prove an actual time lag.")
        save(rawdir/(c["id"]+"_request.json"),{"messages":msgs,"model":old_critic.MODEL})
        try:
            provider,raw=old_critic.call(account,token,msgs)
            save(rawdir/(c["id"]+"_provider_original.json"),provider)
            (rawdir/(c["id"]+"_response.txt")).write_text(raw,encoding="utf-8")
            proposal=old_critic.parse(raw)
            lint=old_critic.validate(payload,proposal)
            admitted=lint["status"]=="VALID_FORMAT"
            if admitted:
                baseline_kept=old_critic.apply(proposal,{
                    t:{n:("LAG" if v=="DISTINCT" else v) for n,v in dic.items()}
                    for t,dic in sig.items()})["survivors_conditional_on_critic_premises"]
            else:baseline_kept=list(sorted(ALL))
            baseline.append({"case_id":c["id"],"admitted":admitted,"linter":lint,
                "proposed":proposal if admitted else "INVALID",
                "baseline_survivors":baseline_kept,"guard_survivors":r["survivors_measured_only"],
                "baseline_false_elimination":truth[c["id"]] not in baseline_kept,
                "guard_false_elimination":r["false_elimination"]})
        except Exception as exc:
            baseline.append({"case_id":c["id"],"admitted":False,
                "error_type":type(exc).__name__,"baseline_survivors":None,
                "guard_survivors":r["survivors_measured_only"]})
        save(out/"llama_cases.json",baseline)
    complete=[r for r in baseline if r["baseline_survivors"] is not None]
    score={"status":"COMPLETE" if len(complete)==len(cases) else "PARTIAL",
           "n_attempted":len(cases),"n_scored":len(complete),
           "baseline_false_eliminations":sum(r["baseline_false_elimination"] for r in complete),
           "guard_false_eliminations_on_same_cases":sum(r["guard_false_elimination"] for r in complete),
           "baseline_average_remaining":sum(len(r["baseline_survivors"]) for r in complete)/len(complete) if complete else None,
           "guard_average_remaining":sum(len(r["guard_survivors"]) for r in complete)/len(complete) if complete else None,
           "semantic_fact_ids_not_verified":True,
           "not_statistically_representative":True}
    save(out/"llama_score.json",score)
    return score

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--series",required=True,type=Path)
    p.add_argument("--probes",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--llama",action="store_true")
    args=p.parse_args()
    print(json.dumps(run(args.series,args.probes,args.out,args.llama),ensure_ascii=False))
if __name__=="__main__":main()
