#!/usr/bin/env python3
"""S2 audit: independent fixed-step Euler reference against two OpenModelica models.

S2 is SYNTHETIC and distinct from S1: accepted orders -> unprepared work ->
prepared orders -> delivered orders. OMC must reuse SystemDynamics stocks and
bounded rates; the Python reference uses explicit balance updates without PySD.
"""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path

HERE=Path(__file__).resolve().parent
FIELDS=("acceptedRate","preparationRate","dispatchRate",
        "unpreparedOrders","preparedOrders","deliveredOrders")
STOCKS=("unpreparedOrders","preparedOrders","deliveredOrders")
RATES=("acceptedRate","preparationRate","dispatchRate")

def scenario():
    return json.loads((HERE/"scenario.json").read_text(encoding="utf-8"))

def rate_at(t,cfg):
    for item in cfg["arrival_regimes"]:
        if item["start_hour"]<=t<item["end_hour"]:return float(item["accepted_orders_per_hour"])
    return 0.

def independent_reference(cfg):
    dt=float(cfg["dt_hours"])
    n=round(float(cfg["duration_hours"])/dt)
    assert n==40 and dt==0.25
    prep_cap=float(cfg["capacity_preparing_orders_per_hour"])
    ship_cap=float(cfg["capacity_dispatch_orders_per_hour"])
    prep_tau=float(cfg["preparation_response_time_hours"])
    ship_tau=float(cfg["dispatch_response_time_hours"])
    assert prep_tau>=dt and ship_tau>=dt
    work=float(cfg["initial_unprepared_orders"])
    stock=float(cfg["initial_prepared_orders"])
    delivered=float(cfg["initial_delivered_orders"])
    out=[]
    for i in range(n+1):
        t=i*dt
        orders=rate_at(t,cfg)
        prepare=min(prep_cap,max(0,work/prep_tau))
        ship=min(ship_cap,max(0,stock/ship_tau))
        out.append({"time":t,"acceptedRate":orders,
            "preparationRate":prepare,"dispatchRate":ship,
            "unpreparedOrders":work,"preparedOrders":stock,"deliveredOrders":delivered})
        if i<n:
            work+=dt*(orders-prepare)
            stock+=dt*(prepare-ship)
            delivered+=dt*ship
    return out

def read_csv(path,modelica=False):
    with Path(path).open(encoding="utf-8-sig",newline="") as h:
        data=list(csv.DictReader(h))
    if modelica:
        # OMC emits pre-event and post-event samples for discontinuities at 2h
        # and 4h, plus sometimes an extra terminal row. Retain the LAST sample
        # at each exact grid timestamp, i.e., the right-continuous event state.
        # Reject off-grid observations or unexpected event duplicates.
        by_step={}
        duplicates=[]
        for row in data:
            t=float(row["time"])
            k=round(t/.25)
            if not (0<=k<=40 and abs(t-k*.25)<1e-7):
                raise ValueError(f"UNEXPECTED_OFF_GRID_TIMESTAMP:{t}")
            if k in by_step:
                if k not in (8,16,40):
                    raise ValueError(f"UNEXPECTED_DUPLICATE_TIMESTAMP:{t}")
                duplicates.append(k)
            by_step[k]=row
        if len(data)>41:
            print("OMC_DISCONTINUITY_RECORDS",json.dumps({"source":str(path),
                "raw_rows":len(data),"duplicate_event_times":[k*.25 for k in duplicates]}),flush=True)
        data=[by_step[i] for i in sorted(by_step)]
    if len(data)!=41:raise ValueError(f"REQUIRED_41_TIMES:{path}:got={len(data)}")
    if not all(abs(float(r["time"])-i*.25)<1e-7 for i,r in enumerate(data)):
        raise ValueError(f"TIMESTAMP_MISMATCH:{path}")
    return data

def field(row,key):
    if key in row:return float(row[key])
    alt=[v for k,v in row.items() if k.endswith("."+key)]
    if len(alt)==1:return float(alt[0])
    raise ValueError(f"FIELD_NOT_FOUND_OR_AMBIGUOUS:{key}:{list(row)}")

def pair(a,b,name,tolerance):
    diffs={}
    for k in FIELDS:
        items=[abs(field(x,k)-field(y,k)) for x,y in zip(a,b)]
        if not all(math.isfinite(v) for v in items):
            raise ValueError("NON_FINITE:"+name+":"+k)
        diffs[k]={"max_abs_error":max(items),
                  "max_at_time":.25*items.index(max(items)),
                  "pass":max(items)<=tolerance}
    return {"pair":name,"pass":all(x["pass"] for x in diffs.values()),"fields":diffs}

def check_invariants(rows,label,cfg,tol=1e-7):
    dt=cfg["dt_hours"]
    prep_cap=cfg["capacity_preparing_orders_per_hour"]
    ship_cap=cfg["capacity_dispatch_orders_per_hour"]
    checks={"nonnegative_stocks":True,"nonnegative_rates":True,
            "bounded_preparation":True,"bounded_dispatch":True,
            "stock_conservation":True,"delivered_nondecreasing":True,
            "no_processing_when_work_empty":True,"arrivals_stop_at_four":True,
            "backlog_drains_after_stop":True,"surge_creates_work_backlog":True}
    total=cfg["initial_unprepared_orders"]+cfg["initial_prepared_orders"]+cfg["initial_delivered_orders"]
    w4=None;wlast=None;max_balance_error=0.
    for i,r in enumerate(rows):
        t=float(r["time"])
        values={x:field(r,x) for x in FIELDS}
        if any(not math.isfinite(x) for x in values.values()):
            raise ValueError(label+":nonfinite")
        checks["nonnegative_stocks"] &= all(values[k]>=-tol for k in STOCKS)
        checks["nonnegative_rates"] &= all(values[k]>=-tol for k in RATES)
        checks["bounded_preparation"] &= values["preparationRate"]<=prep_cap+tol
        checks["bounded_dispatch"] &= values["dispatchRate"]<=ship_cap+tol
        checks["no_processing_when_work_empty"] &= not (values["unpreparedOrders"]<tol and values["preparationRate"]>tol)
        if i>0:
            checks["delivered_nondecreasing"] &= values["deliveredOrders"]>=field(rows[i-1],"deliveredOrders")-tol
        if t>=4:
            checks["arrivals_stop_at_four"] &= values["acceptedRate"]<=tol
        if abs(t-4)<1e-8:w4=values["unpreparedOrders"]
        if i==len(rows)-1:wlast=values["unpreparedOrders"]
        balance=values["unpreparedOrders"]+values["preparedOrders"]+values["deliveredOrders"]-total
        max_balance_error=max(max_balance_error,abs(balance))
        checks["stock_conservation"] &= abs(balance)<tol
        if i<len(rows)-1:total+=dt*values["acceptedRate"]
    checks["surge_creates_work_backlog"]=w4 is not None and w4>1
    checks["backlog_drains_after_stop"]=w4 is not None and wlast is not None and wlast < w4
    return {"name":label,"checks":checks,"max_balance_absolute_error":max_balance_error,
            "all_pass":all(checks.values()),
            "final_work":wlast,"work_at_stop":w4,
            "end_delivered":field(rows[-1],"deliveredOrders"),
            "end_prepared":field(rows[-1],"preparedOrders")}

def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as h:
        wr=csv.DictWriter(h,fieldnames=["time",*FIELDS])
        wr.writeheader();wr.writerows(rows)

def audit_component_reuse():
    txt=(HERE/"IGCS2MakeToOrder.mo").read_text()
    block=txt.split("  model Components",1)[1].split("  end Components;",1)[0]
    equation=txt.split("  model Equations",1)[1].split("  end Equations;",1)[0]
    source={
     "scenario":"S2 synthetic make-to-order, not Hines S1",
     "preexisting_library_stock_components":{
       "Level":block.count("SystemDynamics.Levels.Level "),
       "Level1a":block.count("SystemDynamics.Levels.Level1a ")},
     "preexisting_library_rate_components":{
       "Rate_1":block.count("SystemDynamics.Rates.Rate_1 "),
       "RRate":block.count("SystemDynamics.Rates.RRate ")},
     "connections_explicit":block.count("connect("),
     "differential_equations_authored_in_component_model":block.count("der("),
     "differential_equations_authored_in_equation_model":equation.count("der("),
     "domain_logic_still_authored":["piecewise accepted-order arrival schedule",
       "two proportional response policies with nonnegative truncation",
       "separate capacity limits and stock semantics"],
     "estimated_authoring_time_or_effort_saved":"NOT_MEASURED",
     "independent_validation_of_business_mechanism":"NOT_DONE",
     "library_usage_means_industrial_accuracy":False
    }
    return source

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--reference-out",type=Path,required=True)
    p.add_argument("--equations",type=Path)
    p.add_argument("--components",type=Path)
    p.add_argument("--report",type=Path)
    a=p.parse_args()
    cfg=scenario()
    ref=independent_reference(cfg)
    write_csv(a.reference_out,ref)
    if not a.equations and not a.components:
        print("S2_REFERENCE_READY",len(ref),"times, independent Euler",flush=True)
        return
    if not a.equations or not a.components or not a.report:
        raise ValueError("BOTH_OMC_CSVS_AND_REPORT_REQUIRED")
    eq=read_csv(a.equations,modelica=True)
    comp=read_csv(a.components,modelica=True)
    reference=read_csv(a.reference_out)
    pairs=[
       pair(reference,eq,"REFERENCE_VS_OMC_EQUATIONS",1e-6),
       pair(reference,comp,"REFERENCE_VS_OMC_COMPONENTS",1e-6),
       pair(eq,comp,"OMC_EQUATIONS_VS_COMPONENTS",1e-6)]
    invariants=[check_invariants(rows,name,cfg) for name,rows in
                ((reference,"INDEPENDENT_PYTHON_EULER"),(eq,"OMC_EQUATIONS"),(comp,"OMC_COMPONENTS"))]
    report={"status":"PASS" if all(x["pass"] for x in pairs) and all(x["all_pass"] for x in invariants) else "MISMATCH",
       "experiment":"IGC_S2_MTO_COMPONENT_REUSE_V1",
       "inputs":cfg,"scope":"synthetic accepted orders only, no real business claim",
       "tolerance_abs":1e-6,"comparisons":pairs,"invariants":invariants,
       "reuse_inventory":audit_component_reuse(),
       "source_modelica":"BSD SystemDynamics 2.1.2 + independently authored policy",
       "no_hines_mdl_bytes_used":True}
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("S2_COMPONENT_COMPARISON",json.dumps({"status":report["status"],
        "max_pair_errors":{p["pair"]:max(x["max_abs_error"] for x in p["fields"].values()) for p in pairs},
        "all_invariants":all(x["all_pass"] for x in invariants)},ensure_ascii=False),flush=True)
    if report["status"]!="PASS":raise SystemExit(1)

if __name__=="__main__":main()
