#!/usr/bin/env python3
"""IGC robustness probe: bounded sensor error vs PR30-style exact threshold.

The mechanism ground truth is loaded only for simulation selection/scoring.
No model label or hidden parameter is exposed to classify_observations().
All data SIMULATED by OpenModelica + seeded measurement perturbations.
"""
from __future__ import annotations
import argparse,hashlib,json,math,random,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/"observability-provenance-v1"))
from observability import PAIRS,ALL,convert_signatures,read,save
sys.path.insert(0,str(ROOT.parent/"dual-mechanism-v1"))
from analyze import rows, col
SERIES=("dispatchRate","deliveryRate","reportedDeliveryRate")
CONDITIONS=("CLEAN_ALL","BOUNDED_ALL","SPARSE_ALL","MISSING_RECEIPT","BAD_CALIBRATION")
WORLDS=("Fast","Slow")
MIN_COMMON=8
DT=0.125
BOUND=0.03
ABS_TOL=1e-6

def case_specs():
    """Forty fixed cases, without true graph names in the public manifest."""
    ids=[f"N{i:02d}" for i in range(1,41)]
    return [{"id":ids[idx],"condition":condition,
             "declared_sampling":"shared regular 0.125-hour grid with per-channel gaps",
             "noise_contract":"bounded uniform amplitude 0.03 (or exact in CLEAN_ALL)",
             "sources":{"dispatchRate":"dispatch-erp","deliveryRate":"customer-receipt-scan",
                        "reportedDeliveryRate":"dashboard-metrics"}}
            for idx,(_,_,condition) in enumerate(
                (g,w,c) for w in WORLDS for g in ("Direct","TransitOnly","ReportOnly","TransitAndReport")
                for c in CONDITIONS)]

def truth_index():
    specs=case_specs()
    combos=[(g,w,c) for w in WORLDS for g in ("Direct","TransitOnly","ReportOnly","TransitAndReport") for c in CONDITIONS]
    return {case["id"]:{"graph":graph,"world":world,"condition":condition} for case,(graph,world,condition) in zip(specs,combos)}

def time_aligned_rates(table):
    """Use last sample at each nominal grid point; preserve event ordering."""
    points={}
    for r in table:
        t=r["time"]
        if not math.isfinite(t):raise ValueError("NONFINITE_TIME")
        tick=round(t/DT)
        if 0<=tick<=64 and abs(t-tick*DT)<1e-7:
            points[tick]={name:col(r,name) for name in SERIES}
    if set(points)!=set(range(65)):raise ValueError("INCOMPLETE_OM_GRID")
    if any(not math.isfinite(v) for point in points.values() for v in point.values()):
        raise ValueError("NONFINITE_SOURCE")
    return points

def rng_for(cid,signal):
    seed=int(hashlib.sha256((cid+"|"+signal+"|IGC_STRESS_V1").encode()).hexdigest()[:16],16)
    return random.Random(seed)

def make_observations(case,table):
    data=time_aligned_rates(table)
    condition=case["condition"]
    available=[x for x in SERIES if not(condition=="MISSING_RECEIPT" and x=="deliveryRate")]
    channels={}
    for name in available:
        rg=rng_for(case["id"],name)
        noise=0. if condition=="CLEAN_ALL" else BOUND
        gain=1.3 if (condition=="BAD_CALIBRATION" and name=="reportedDeliveryRate") else 1.
        quality="UNCALIBRATED_GAIN" if gain!=1. else "CALIBRATED"
        by_tick={}
        for tick in sorted(data):
            # Per-channel missed packets. Never impute missing values.
            if condition=="SPARSE_ALL" and rg.random()<0.45:continue
            err=rg.uniform(-noise,noise) if noise else 0.
            by_tick[str(tick)]=round(data[tick][name]*gain+err,10)
        channels[name]={
            "values_by_tick":by_tick,"unit":"orders/hour","channel":case["sources"][name],
            "quality":quality,"certified_abs_error_bound":noise if quality=="CALIBRATED" else None,
            "provenance":"OM_PLUS_SYNTHETIC_SENSOR","calibration_claim":"ASSUMED_FOR_BENCHMARK"}
    return {"case_id":case["id"],"condition":condition,
            "time_grid":{"start":0,"end":8,"step_hours":DT,"clock":"synthetic_aligned"},
            "channels":channels,"not_real_company_observations":True}

def validate_packet(packet):
    if not isinstance(packet,dict) or set(packet["channels"])-set(SERIES):
        raise ValueError("UNKNOWN_CHANNEL")
    for name,c in packet["channels"].items():
        if c["unit"]!="orders/hour":raise ValueError("INCOMPATIBLE_UNIT")
        if not c["channel"] or not isinstance(c["values_by_tick"],dict):raise ValueError("BAD_CHANNEL")
        if not c.get("quality") in ("CALIBRATED","UNCALIBRATED_GAIN"):raise ValueError("BAD_QUALITY")
        for tick,value in c["values_by_tick"].items():
            try:i=int(tick)
            except (TypeError,ValueError):raise ValueError("INVALID_TICK")
            if str(i)!=tick or i<0 or i>64 or not isinstance(value,(int,float)) or not math.isfinite(value):
                raise ValueError("BAD_SAMPLE")
        b=c["certified_abs_error_bound"]
        if c["quality"]=="CALIBRATED" and (b is None or b<0 or not math.isfinite(b)):
            raise ValueError("MISSING_CALIBRATION_BOUND")
        if c["quality"]!="CALIBRATED" and b is not None:
            raise ValueError("CONFLICTING_CALIBRATION")
    if len({x["channel"] for x in packet["channels"].values()})!=len(packet["channels"]):
        raise ValueError("SAME_SOURCE_REUSED")

def compare_channels(a,b,mode):
    overlap=sorted(set(a["values_by_tick"])&set(b["values_by_tick"]),key=int)
    if len(overlap)<MIN_COMMON:
        return {"status":"UNKNOWN","reason":"INSUFFICIENT_OVERLAP","common_samples":len(overlap)}
    max_d=max(abs(a["values_by_tick"][i]-b["values_by_tick"][i]) for i in overlap)
    if mode=="naive":
        return {"status":"SYNC" if max_d<=ABS_TOL else "DISTINCT",
                "max_difference":max_d,"common_samples":len(overlap),
                "reason":"PR30_STYLE_FIXED_TOLERANCE"}
    if a["quality"]!="CALIBRATED" or b["quality"]!="CALIBRATED":
        return {"status":"INCONCLUSIVE","reason":"UNCERTIFIED_SENSOR",
                "max_difference":max_d,"common_samples":len(overlap)}
    envelope=a["certified_abs_error_bound"]+b["certified_abs_error_bound"]+ABS_TOL
    return {"status":"PROVEN_DISTINCT" if max_d>envelope else "INCONCLUSIVE",
            "max_difference":max_d,"envelope":envelope,"common_samples":len(overlap),
            "reason":"BOUNDED_DIFFERENCE_FROM_EQUALITY"}

def classify_observations(packet,signatures,mode):
    """No truth, model variants or hidden parameters are accepted here."""
    validate_packet(packet)
    if mode not in ("naive","bounded"):raise ValueError("UNKNOWN_METHOD")
    checks={};candidates=set(ALL)
    for name,(left,right) in PAIRS.items():
        if left not in packet["channels"] or right not in packet["channels"]:
            checks[name]={"status":"UNKNOWN","reason":"CHANNEL_MISSING"}
            continue
        a=packet["channels"][left];b=packet["channels"][right]
        result=compare_channels(a,b,mode)
        checks[name]=result
        if mode=="naive" and result["status"] in ("SYNC","DISTINCT"):
            candidates={g for g in candidates if signatures[name][g]==result["status"]}
        if mode=="bounded" and result["status"]=="PROVEN_DISTINCT":
            candidates={g for g in candidates if signatures[name][g]=="DISTINCT"}
    return {"survivors":sorted(candidates),"checks":checks,
            "abstained":len(candidates)!=1,"no_candidate":not bool(candidates),
            "rule":"no inferred equality from noisy agreement" if mode=="bounded"
                   else "hard threshold on pairwise sampled differences"}

def score(results):
    def stats(key):
        pairs=[(x["truth"]["graph"],x[key]) for x in results]
        return {"false_eliminations":sum(g not in p["survivors"] for g,p in pairs),
            "empty_sets":sum(not p["survivors"] for _,p in pairs),
            "singletons":sum(len(p["survivors"])==1 for _,p in pairs),
            "mean_survivors":round(sum(len(p["survivors"]) for _,p in pairs)/len(pairs),4)}
    by_condition={}
    for cond in CONDITIONS:
        sub=[x for x in results if x["condition"]==cond]
        by_condition[cond]={"n":len(sub),"naive":stats_for(sub,"naive"),"bounded":stats_for(sub,"bounded")}
    return {"n":len(results),"baseline":stats("naive"),"bounded":stats("bounded"),
            "by_condition":by_condition,
            "source":"OpenModelica held-out parameter worlds and deterministic bounded sensor noise",
            "real_company_data":False,"parameters_visible_to_classifier":False,
            "claims_of_model_identification":"NONE"}

def stats_for(results,key):
    return {"false_eliminations":sum(r["truth"]["graph"] not in r[key]["survivors"] for r in results),
            "mean_survivors":round(sum(len(r[key]["survivors"]) for r in results)/len(results),4),
            "singletons":sum(len(r[key]["survivors"])==1 for r in results)}

def run(folder,probe_path,out):
    cases=case_specs();truth=truth_index()
    if len(cases)!=40 or len(truth)!=40:raise ValueError("CAMPAIGN_SIZE")
    signatures=convert_signatures(read(probe_path))
    base=Path(folder);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    outputs=[];packets=[]
    for case in cases:
        hidden=truth[case["id"]]
        file=base/("stress_"+hidden["world"]+hidden["graph"]+"_res.csv")
        obs=make_observations(case,rows(file))
        packets.append(obs)
        baseline=classify_observations(obs,signatures,"naive")
        bounded=classify_observations(obs,signatures,"bounded")
        outputs.append({"case_id":case["id"],"condition":case["condition"],
                        "truth":hidden,"naive":baseline,"bounded":bounded})
    save(out/"observations_no_truth.json",packets)
    save(out/"evaluations_with_truth.json",outputs)
    metrics=score(outputs);save(out/"score.json",metrics)
    # This is a gate, not an after-the-fact change to gold.
    if metrics["bounded"]["false_eliminations"]!=0:
        raise AssertionError("BOUNDED_GUARD_FALSE_ELIMINATION")
    if metrics["baseline"]["false_eliminations"]==0:
        raise AssertionError("NEGATIVE_CONTROL_NOT_ACTIVATED")
    if metrics["bounded"]["mean_survivors"]>=4:
        raise AssertionError("GUARD_NEVER_DISCRIMINATES")
    print("IGC_NOISE_PARAM_SCORES",json.dumps(metrics,ensure_ascii=False),flush=True)
    return metrics

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--series",required=True,type=Path)
    p.add_argument("--probes",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args();run(a.series,a.probes,a.out)
