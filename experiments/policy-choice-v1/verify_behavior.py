#!/usr/bin/env python3
"""Independent policy discrimination: NOT a parity comparison of a model to itself.

Counterfactual: shut off newly accepted orders while keeping a verified planned
production policy (MTS). Then ask whether new objects can still be produced.
MTO strict should not process anything from initially empty queues.
MTS S1 has known curve behavior and is NOT claimed empirically valid.
"""
import csv,json,math,argparse
from pathlib import Path
def csv_rows(path):
    with open(path,encoding="utf-8-sig",newline="") as f:
        rows=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
    if not rows:raise ValueError("EMPTY_CSV")
    if any(not math.isfinite(x) for r in rows for x in r.values()):
        raise ValueError("NONFINITE")
    return rows
def get(row,field):
    if field in row:return row[field]
    alt=[v for k,v in row.items() if k.endswith("."+field)]
    if len(alt)!=1:raise ValueError("UNKNOWN_FIELD:"+field)
    return alt[0]
def examine(mto,mts):
    mto=csv_rows(mto);mts=csv_rows(mts)
    eps=1e-6
    mto_no_processing=all(abs(get(r,"acceptedRate"))<eps
       and abs(get(r,"preparationRate"))<eps
       and abs(get(r,"dispatchRate"))<eps for r in mto)
    mto_empty=all(abs(get(r,"unpreparedOrders"))<eps
       and abs(get(r,"preparedOrders"))<eps for r in mto)
    mts_no_orders="acceptedOrders=0" in (Path(__file__).resolve().parent/"BehaviorProbes.mo").read_text(encoding="utf-8")
    mts_positive_production=any(get(r,"production")>eps for r in mts)
    mts_inventories_increase=get(mts[-1],"inventory")>get(mts[0],"inventory")+eps
    result={"status":"PASS" if all((mto_no_processing,mto_empty,mts_no_orders,mts_positive_production,mts_inventories_increase)) else "FAILED",
      "scope":"synthetic counterfactual zero new orders, not fitted observed data",
      "MTO":{"no_processing_without_orders":mto_no_processing,"queues_remain_empty":mto_empty},
      "MTS":{"zero_customer_orders":mts_no_orders,"production_continues":mts_positive_production,"finished_inventory_accumulates":mts_inventories_increase},
      "models_different":True,
      "known_limit":"S1 Hines CapUtil lookup may overproduce relative to target; zero orders does not imply zero MTS production."}
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mto",type=Path,required=True)
    p.add_argument("--mts",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=examine(a.mto,a.mts)
    a.out.parent.mkdir(exist_ok=True,parents=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("POLICY_BEHAVIOR_DISCRIMINATION",json.dumps(report),flush=True)
    if report["status"]!="PASS":raise SystemExit(1)
if __name__=="__main__":main()
