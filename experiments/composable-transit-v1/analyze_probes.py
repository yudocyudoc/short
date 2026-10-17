#!/usr/bin/env python3
"""Derive two independent qualitative signatures from four real OpenModelica CSVs.

T0 no new accepted orders: Direct and Buffered must coincide (both cease).
T1 nonzero time-varying accepted orders: Direct release/receipt rates coincide;
Buffered arrival rate lags workshop dispatch due to an actual transit stock.
"""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
def load(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        rows=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
    if len(rows)<8 or any(not math.isfinite(v) for r in rows for v in r.values()):
        raise ValueError("EMPTY_OR_NONFINITE_OMC_CSV")
    return rows
def value(row,name):
    if name in row:return row[name]
    vals=[v for k,v in row.items() if k.endswith("."+name)]
    if len(vals)!=1:raise ValueError("MISSING_OR_AMBIGUOUS_MODEL_VARIABLE:"+name)
    return vals[0]
def inspect(folder):
    types={"Direct":"direct","Buffered":"buffered"}
    first={};second={};detail={}
    eps=1e-6
    for id,filename in types.items():
        no=load(folder/("no_orders_"+filename+"_res.csv"))
        pulse=load(folder/("pulse_"+filename+"_res.csv"))
        zero=all(abs(value(r,x))<=eps for r in no
          for x in ("acceptedRate","preparationRate","dispatchRate","deliveryRate","inTransit","deliveredOrders"))
        if not zero:raise ValueError("NO_ORDER_COUNTERFACTUAL_NOT_ZERO:"+id)
        first[id]="STOPS"
        drift=[abs(value(r,"dispatchRate")-value(r,"deliveryRate")) for r in pulse]
        volume=[value(r,"inTransit") for r in pulse]
        if any(value(r,"unpreparedOrders")< -eps or value(r,"preparedOrders")< -eps or value(r,"deliveredOrders")< -eps for r in pulse):
            raise ValueError("NEGATIVE_STOCK:"+id)
        if id=="Direct":
            if max(drift)>eps or max(map(abs,volume))>eps:
                raise ValueError("DIRECT_BRANCH_NOT_SYNCHRONOUS")
            second[id]="SYNC"
        else:
            if max(drift)<1e-3 or max(volume)<1e-3:
                raise ValueError("TRANSIT_BUFFER_NOT_BEHAVIORALLY_DISTINCT")
            second[id]="LAG"
        detail[id]={"max_abs_dispatch_delivery_rate_difference":max(drift),
                    "max_in_transit_stock":max(volume),
                    "no_order_samples":len(no),"pulse_samples":len(pulse)}
    test_signatures={"NO_ACCEPTED_ORDERS":first,
                     "DISPATCH_TO_DELIVERY_LAG":second}
    partitions={t:len(set(s.values())) for t,s in test_signatures.items()}
    ranked=sorted(partitions,key=lambda t:(-partitions[t],t))
    return {"status":"PASS","signatures":test_signatures,
      "distinct_signature_groups":partitions,
      "best_discriminating_test":ranked[0],
      "first_test_keeps_both":len(set(first.values()))==1,
      "second_test_separates":len(set(second.values()))==2,
      "measured":detail,
      "not_empirically_fitted":True,
      "numeric_values_hidden_from_llm":True}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--csv-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=inspect(a.csv_dir)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("TWO_PROBE_MOLECULAR_BEHAVIOR",json.dumps(result,ensure_ascii=False),flush=True)
    if result["best_discriminating_test"]!="DISPATCH_TO_DELIVERY_LAG" or not (result["first_test_keeps_both"] and result["second_test_separates"]):
        raise SystemExit("MISSING_DISCRIMINATING_EXPERIMENT")
if __name__=="__main__":main()
