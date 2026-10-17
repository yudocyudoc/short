#!/usr/bin/env python3
"""Observe real OpenModelica outputs, not a declared oracle graph.

Two distinct mechanisms can create the same binary 'observed lag' signature.
Full numerical equivalence is NOT claimed from binary qualitative grouping.
"""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
NAMES=("Direct","ReportOnly","TransitOnly","TransitAndReport")
TESTS=("OBSERVED_VS_DISPATCH","PHYSICAL_VS_DISPATCH","OBSERVED_VS_PHYSICAL")
TOL=1e-6
def rows(filename):
    with Path(filename).open(encoding="utf-8-sig",newline="") as f:
        data=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
    if len(data)<10 or any(not math.isfinite(v) for r in data for v in r.values()):
        raise ValueError("BAD_OPENMODELICA_SERIES:"+str(filename))
    return data
def col(row,name):
    if name in row:return row[name]
    hits=[v for k,v in row.items() if k.endswith("."+name)]
    if len(hits)!=1:raise ValueError("AMBIGUOUS_VARIABLE:"+name)
    return hits[0]
def sig(data,first,second):
    dif=max(abs(col(r,first)-col(r,second)) for r in data)
    return ("SYNC" if dif<=TOL else "LAG"),dif
def split_quality(signatures,case_ids,test):
    """Balanced partition (Gini) and number of groups; deterministic tie-break."""
    n=len(case_ids)
    groups={}
    for cid in case_ids:groups[signatures[test][cid]]=groups.get(signatures[test][cid],0)+1
    return (1-sum((x/n)**2 for x in groups.values()),len(groups))
def next_experiment(signatures,remaining,known=()):
    available=[t for t in TESTS if t not in known]
    if len(remaining)<=1 or not available:return None
    opts=sorted(available,key=lambda t:(-split_quality(signatures,remaining,t)[0],
                                       -split_quality(signatures,remaining,t)[1],t))
    return opts[0] if split_quality(signatures,remaining,opts[0])[1]>1 else None
def inspect(folder):
    signatures={t:{} for t in TESTS};details={}
    data={}
    for name in NAMES:
        zero=rows(folder/("zero_"+name+"_res.csv"))
        pulse=rows(folder/("pulse_"+name+"_res.csv"))
        data[name]=pulse
        for r in zero:
            for field in ("acceptedRate","preparationRate","dispatchRate","deliveryRate",
                          "reportedDeliveryRate","inTransit","deliveredOrders"):
                if abs(col(r,field))>TOL:raise ValueError("NONZERO_ZERO_ORDER_"+name+":"+field)
        for r in pulse:
            for field in ("unpreparedOrders","preparedOrders","deliveredOrders","inTransit"):
                if col(r,field)<-TOL:raise ValueError("NEGATIVE_STOCK_"+name+":"+field)
        detail={}
        for test,left,right in [
          (TESTS[0],"dispatchRate","reportedDeliveryRate"),
          (TESTS[1],"dispatchRate","deliveryRate"),
          (TESTS[2],"deliveryRate","reportedDeliveryRate")]:
            status,delta=sig(pulse,left,right)
            signatures[test][name]=status
            detail[test]={"signature":status,"max_abs_rate_difference":delta}
        detail["max_in_transit"]=max(col(r,"inTransit") for r in pulse)
        details[name]=detail
    # Independent module: purely informational reporting must not modify
    # physical arrival (nor counts) at otherwise identical physical settings.
    for a,b in (("Direct","ReportOnly"),("TransitOnly","TransitAndReport")):
        if len(data[a])!=len(data[b]):raise ValueError("UNEQUAL_SAMPLE_GRID")
        for ra,rb in zip(data[a],data[b]):
            for field in ("deliveryRate","deliveredOrders","dispatchRate","inTransit"):
                if abs(col(ra,field)-col(rb,field))>TOL:
                    raise ValueError("REPORT_FILTER_ALTERED_PHYSICAL_MATERIAL_FLOW:"+field)
    expected={
      "Direct":("SYNC","SYNC","SYNC"),
      "ReportOnly":("LAG","SYNC","LAG"),
      "TransitOnly":("LAG","LAG","SYNC"),
      "TransitAndReport":("LAG","LAG","LAG")
    }
    for name,vector in expected.items():
        actual=tuple(signatures[t][name] for t in TESTS)
        if actual!=vector:
            raise ValueError("INCORRECT_MOLECULAR_SIGNATURE:"+name+":"+str(actual))
    if not (details["TransitOnly"]["max_in_transit"]>0.1 and
            details["TransitAndReport"]["max_in_transit"]>0.1 and
            max(details["Direct"]["max_in_transit"],details["ReportOnly"]["max_in_transit"])<=TOL):
        raise ValueError("TRANSIT_BUFFER_NOT_VERIFIED")
    first=TESTS[0]
    observed_lag=sorted(n for n in NAMES if signatures[first][n]=="LAG")
    next_test=next_experiment(signatures,observed_lag,(first,))
    if len(observed_lag)!=3 or next_test is None:raise ValueError("NO_SECOND_STAGE_PARTITION")
    return {
      "status":"PASS",
      "signatures":signatures,
      "detail":details,
      "first_test":first,
      "survivors_if_observed_lag":observed_lag,
      "next_test_on_three_remaining":next_test,
      "next_test_partition_quality":split_quality(signatures,observed_lag,next_test),
      "all_four_joint_signatures_distinct":len({tuple(signatures[t][n] for t in TESTS) for n in NAMES})==4,
      "numeric_equivalence_not_claimed":True,
      "physical_measured_vs_latent_visibility_matters":True,
      "llm_saw_no_numerical_values":True
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--directory",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=inspect(a.directory)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("DUAL_MOLECULAR_OBSERVABILITY",json.dumps({
      "status":result["status"],"signatures":result["signatures"],
      "survivors":result["survivors_if_observed_lag"],
      "next_test":result["next_test_on_three_remaining"]},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
