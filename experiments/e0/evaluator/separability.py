#!/usr/bin/env python3
"""E0 evaluator-only numeric separability audit; no truth key or expected signature table."""
import argparse
import csv
import itertools
import json
import math
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
PHYSICAL=("dispatchRate","deliveryRate","inTransit")
REFERENCE=("ZeroDirect","ZeroFilter","OneDirect","OneFilter","TwoDirect","TwoFilter")


def value(row,field):
    matches=[float(v) for k,v in row.items() if k==field or k.endswith("."+field)]
    if len(matches)!=1 or not math.isfinite(matches[0]):
        raise ValueError("AMBIGUOUS_OR_INVALID_FIELD:"+field)
    return matches[0]


def read_csv(path):
    with Path(path).open(newline="",encoding="utf-8-sig") as f:
        rows=list(csv.DictReader(f))
    result=[]
    for row in rows:
        time=value(row,"time")
        if result and time<value(result[-1],"time")-1e-8:
            raise ValueError("TIME_NOT_MONOTONIC")
        if result and abs(time-value(result[-1],"time"))<1e-8:
            result[-1]=row
        else:
            result.append(row)
        for field in (*PHYSICAL,"reportedDeliveryRate"):
            value(row,field)
    if len(result)<100:
        raise ValueError("TOO_FEW_OBSERVATIONS")
    return result


def compare(left,right,fields):
    if len(left)!=len(right):
        raise ValueError("INCOMPATIBLE_GRIDS")
    differences=[]
    for a,b in zip(left,right):
        if abs(value(a,"time")-value(b,"time"))>1e-8:
            raise ValueError("UNALIGNED_TIME_GRIDS")
        for field in fields:
            differences.append(abs(value(a,field)-value(b,field)))
    return {"max_abs_difference":max(differences),
            "rmse_difference":math.sqrt(sum(x*x for x in differences)/len(differences))}


def classify(result,error_bound):
    if error_bound<=0:raise ValueError("INVALID_ERROR_BOUND")
    if result["max_abs_difference"]>error_bound:
        return "SEPARABLE_NUMERICALLY"
    return "UNRESOLVED_WITHIN_OPERATIONAL_BOUND"


def assess_cross_parameter(index,left,right,caps,probes,fields,bound):
    """A structure is not refuted when *some other allowed parameters* fit."""
    combinations=[]
    for left_cap in caps:
        for right_cap in caps:
            by_probe={}
            for stimulus in probes:
                delta=compare(index[left,left_cap,stimulus],
                              index[right,right_cap,stimulus],fields)
                by_probe[stimulus]=delta["max_abs_difference"]
            combinations.append({
                "left_cap":left_cap,"right_cap":right_cap,
                "max_difference_over_menu":max(by_probe.values()),
                "status":"SEPARABLE_ON_MENU" if max(by_probe.values())>bound
                         else "UNRESOLVED_ON_MENU",
                "probe_max_differences":by_probe
            })
    all_separated=all(x["status"]=="SEPARABLE_ON_MENU" for x in combinations)
    robust_probes=[probe for probe in probes
                   if all(x["probe_max_differences"][probe]>bound for x in combinations)]
    return {
        "cross_parameter_grid_combinations":len(combinations),
        "status":"SEPARABLE_FOR_ALL_GRID_COMBINATIONS" if all_separated
                 else "UNRESOLVED_PARAMETER_COMPENSATION",
        "robust_single_probes":robust_probes,
        "combinations":combinations,
        "note":"Finite P0 grid ONLY. This cannot exclude continuous parameter compensation."
    }


def run(folder,protocol):
    cases=json.loads((folder.parent/"cases.json").read_text(encoding="utf-8"))
    profiles=protocol["observation_profiles"]
    bound=protocol["numerical"]["error_bound"]
    index={(c["model"],c["cap"],c["probe"]):
           read_csv(folder/(c["name"]+"_res.csv")) for c in cases}
    if len(index)!=len(cases):
        raise ValueError("DUPLICATE_REFERENCE_CASE")
    results=[]
    pairs=list(itertools.combinations(REFERENCE,2))
    for capacity in protocol["parameter_policy"]["transit_capacity_per_h"]:
        for profile_name,profile in profiles.items():
            for left,right in pairs:
                measures=[]
                for stimulus in (q["id"] for q in protocol["interventions"]):
                    diff=compare(index[left,capacity,stimulus],
                                 index[right,capacity,stimulus],profile["visible"])
                    measures.append({"intervention":stimulus,**diff,
                                     "status":classify(diff,bound)})
                separable=any(m["status"]=="SEPARABLE_NUMERICALLY" for m in measures)
                results.append({
                    "pair":[left,right],"capacity_per_h":capacity,
                    "profile":profile_name,
                    "status":"SEPARABLE_ON_TESTED_GRID" if separable else "UNRESOLVED_ON_TESTED_GRID",
                    "interventions":measures,
                    "evidence_type":"computed_from_native_om_csv_not_expected_labels"
                })
    # Stronger question than equal-parameter pair comparisons: can an alternative
    # *with another allowed parameter choice* reproduce the same observations?
    # Cross every left/right parameter setting. A single unresolved combination
    # prevents a claim that the pair is robustly separable under the P0 grid.
    robust=[]
    caps=protocol["parameter_policy"]["transit_capacity_per_h"]
    probes=[q["id"] for q in protocol["interventions"]]
    for profile_name,profile in profiles.items():
        for left,right in pairs:
            robust.append({"pair":[left,right],"profile":profile_name,
                           **assess_cross_parameter(index,left,right,caps,probes,
                                                    profile["visible"],bound)})
    # Independent regression: filter must not alter any physical trace in paired variants.
    max_physical=0
    for c in protocol["parameter_policy"]["transit_capacity_per_h"]:
        for probe in (x["id"] for x in protocol["interventions"]):
            for left,right in (("ZeroDirect","ZeroFilter"),
                               ("OneDirect","OneFilter"),("TwoDirect","TwoFilter")):
                delta=compare(index[left,c,probe],index[right,c,probe],PHYSICAL)["max_abs_difference"]
                max_physical=max(max_physical,delta)
    if max_physical>bound:
        raise ValueError("INFORMATION_FILTER_CHANGED_PHYSICAL_SYSTEM")
    high=max(value(r,"deliveryRate") for r in index["OneDirect",3,"high_pulse"]) if (
        "OneDirect",3,"high_pulse") in index else None
    saturation_verified=high is not None and abs(high-3)<bound*10
    summary=Counter((x["capacity_per_h"],x["profile"],x["status"]) for x in results)
    return {
        "status":"REFERENCE_MATRIX_COMPUTED",
        "methodological_verdict":"ENGINEERING_ONLY",
        "world_identification":"NOT_RUN",
        "structure_classification":"not attempted",
        "numerical_bound":bound,
        "bound_is_certified":False,
        "regime_and_profile_counts":[
            {"capacity_per_h":cap,"profile":p,"separable_pairs":summary[(cap,p,"SEPARABLE_ON_TESTED_GRID")],
             "unresolved_pairs":summary[(cap,p,"UNRESOLVED_ON_TESTED_GRID")]}
            for cap in protocol["parameter_policy"]["transit_capacity_per_h"] for p in profiles],
        "robust_cross_parameter_matrix":robust,
        "robust_cross_parameter_summary":[
            {"profile":p,"robustly_separable":sum(x["status"]=="SEPARABLE_FOR_ALL_GRID_COMBINATIONS"
                for x in robust if x["profile"]==p),
             "unresolved":sum(x["status"]=="UNRESOLVED_PARAMETER_COMPENSATION"
                for x in robust if x["profile"]==p)} for p in profiles],
        "max_physical_delta_if_report_added":max_physical,
        "capacity3_high_pulse_saturation_observed":saturation_verified,
        "reference_cases":len(cases),
        "pair_count":len(results),
        "pairs":results,
        "limitation":"An unresolved numeric pair is NOT certified equivalent; this public evaluator has no secret truth.",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--csv-dir",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    protocol=json.loads((PARENT/"protocol.json").read_text(encoding="utf-8"))
    data=run(args.csv_dir,protocol)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("E0_NUMERIC_REFERENCE",json.dumps({
        "status":data["status"],"matrix":data["regime_and_profile_counts"],
        "parameter_robust":data["robust_cross_parameter_summary"],
        "saturation":data["capacity3_high_pulse_saturation_observed"],
        "max_physical_delta":data["max_physical_delta_if_report_added"],
        "verdict":data["methodological_verdict"]},ensure_ascii=False))


if __name__=="__main__":
    main()
