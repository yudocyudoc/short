#!/usr/bin/env python3
"""Execute only an approved Hines composition in PySD on explicit synthetic data.

Original .mdl sources remain temporary, after SHA-256 verification against the
previously frozen Hines manifests. Never persist the original or adapted .mdl.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,sys
from pathlib import Path
from composer import compile_selection,load

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
HINES=REPO/"experiments/hines-pysd"
SCENARIOS=REPO/"experiments/real-pos/bread-basket/sd-scenarios"

def run(case_id,proposal,originals,scratch,out):
    plan=compile_selection(case_id,proposal)
    out.mkdir(parents=True,exist_ok=True)
    (out/"compiled_plan.json").write_text(json.dumps(plan,indent=2,ensure_ascii=False)+"\n")
    if not plan["safe_to_simulate"]:
        report={"status":"NO_SIMULATION","case_id":case_id,"plan_status":plan["status"],
                "reason":plan.get("reason"),"llm_result_not_overridden":True}
        (out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
        return report
    if case_id!="S1" or plan["scenario"]!="synthetic_mts.json":
        raise ValueError("SIMULATION_SCENARIO_NOT_ALLOWLISTED")
    import pandas as pd
    import pysd
    # The adapter is imported, not rewritten: use the same tested unit-only
    # relabeling code as the previous Bread Basket experiment.
    sys.path.insert(0,str(SCENARIOS))
    from run_scenarios import ephemeral_units

    cfg=load("synthetic_mts.json")
    dt=float(cfg["dt_hours"]);end=float(cfg["duration_hours"])
    if (dt,end)!=(.25,8.0):raise ValueError("UNSUPPORTED_CLOCK")
    ts=[i*dt for i in range(int(end/dt)+1)]
    source_specs=json.loads((HINES/"specifications_extracted.json").read_text())
    scratch.mkdir(parents=True,exist_ok=True)
    ephemeral={}
    for mid in plan["molecules"]:
        file=plan["source_hashes"][mid]["filename"]
        src=originals/file
        expected=source_specs["model_provenance"][file]
        if not src.is_file() or len(src.read_bytes())!=expected["source_bytes"]:
            raise ValueError("MISSING_OR_WRONG_SIZE_SOURCE:"+file)
        if hashlib.sha256(src.read_bytes()).hexdigest()!=expected["source_sha256"]:
            raise ValueError("UNVERIFIED_SOURCE:"+file)
        derived,record=ephemeral_units(file,src,expected["source_sha256"],scratch)
        ephemeral[mid]={"path":derived,"provenance":record}
    # Separate business-policy inputs: planned production is NOT observed sales,
    # orders is an independently specified accepted-order stream.
    plan_rate=float(cfg["planned_production_orders_per_hour"])
    accepted=float(cfg["accepted_orders_per_hour"])
    cap=float(cfg["capacity_orders_per_hour"])
    if not (0<=plan_rate and 0<=accepted and cap>0):raise ValueError("INVALID_RATES")
    production_target=pd.Series([plan_rate]*len(ts),index=ts,dtype="float64")
    accepted_stream=pd.Series([accepted]*len(ts),index=ts,dtype="float64")
    cap_model=pysd.read_vensim(str(ephemeral["CAP_UTIL"]["path"]))
    prod=cap_model.run(params={"Capacity":cap,"Desired Production":production_target},
                       initial_condition="original",time_step=dt,final_time=end,
                       saveper=dt,return_timestamps=ts,
                       return_columns=["Desired Production","Capacity","Production"])
    production=[float(x) for x in prod["Production"]]
    storage_model=pysd.read_vensim(str(ephemeral["BACKLOG_FLOW"]["path"]))
    storage=storage_model.run(
        params={
            "Orders":accepted_stream,
            "Producing":pd.Series(production,index=ts,dtype="float64"),
            "minimum time to ship":float(cfg["assumed_minimum_ship_time_hours"]),
            "Time To Process And Ship Order":float(cfg["assumed_processing_and_shipping_target_hours"])
        },
        initial_condition=(0.0,{"Backlog":float(cfg["initial_accepted_unshipped_orders"]),
                                "Inventory":float(cfg["initial_finished_goods_orders"])}),
        time_step=dt,final_time=end,saveper=dt,return_timestamps=ts,
        return_columns=["Backlog","Inventory","Orders","Producing","Shipping"]
    )
    rows=[]
    for i,t in enumerate(ts):
        r=storage.iloc[i]
        rows.append({"time_hours":t,
             "hypothetical_planned_production_per_hour":plan_rate,
             "hypothetical_accepted_orders_per_hour":accepted,
             "model_production_per_hour":production[i],
             "model_shipping_per_hour":float(r["Shipping"]),
             "model_backlog_orders":float(r["Backlog"]),
             "model_finished_stock_orders":float(r["Inventory"])})
    floats=[v for row in rows for v in row.values()]
    if any(not math.isfinite(v) for v in floats):raise ValueError("NONFINITE_STATE")
    if min(x["model_backlog_orders"] for x in rows)<-1e-7:raise ValueError("NEGATIVE_BACKLOG")
    if min(x["model_finished_stock_orders"] for x in rows)<-1e-7:raise ValueError("NEGATIVE_STOCK")
    n=len(rows)-1
    accepted_total=sum(r["hypothetical_accepted_orders_per_hour"]*dt for r in rows[:n])
    prepared_total=sum(r["model_production_per_hour"]*dt for r in rows[:n])
    shipped_total=sum(r["model_shipping_per_hour"]*dt for r in rows[:n])
    b0=float(cfg["initial_accepted_unshipped_orders"])
    i0=float(cfg["initial_finished_goods_orders"])
    b_err=rows[-1]["model_backlog_orders"]-(b0+accepted_total-shipped_total)
    i_err=rows[-1]["model_finished_stock_orders"]-(i0+prepared_total-shipped_total)
    if max(abs(b_err),abs(i_err))>1e-6:raise ValueError("STOCK_FLOW_BALANCE_MISMATCH")
    with (out/"conditional_timeseries.csv").open("w",newline="",encoding="utf-8") as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result={
       "status":"SYNTHETIC_COMPOSITION_EXECUTED","case_id":case_id,
       "source":"publisher Hines originals SHA-256 checked; temporary unit relabeling only",
       "pysd_version":getattr(pysd,"__version__","unknown"),
       "molecules":plan["molecules"],"typed_wires":plan["wires"],
       "hypothetical_parameters":cfg,
       "hypothetical_accepted_orders_integrated":accepted_total,
       "model_production_integrated":prepared_total,
       "model_shipping_integrated":shipped_total,
       "model_backlog_end":rows[-1]["model_backlog_orders"],
       "model_finished_stock_end":rows[-1]["model_finished_stock_orders"],
       "model_produced_more_than_planned":prepared_total>plan_rate*end+1e-8,
       "conservation_errors":{"backlog":b_err,"finished_stock":i_err},
       "rows":len(rows),
       "source_manifest_sha256":hashlib.sha256((HINES/"specifications_extracted.json").read_bytes()).hexdigest(),
       "evidence_flags":{"synthetic_not_real":True,"parameters_not_calibrated":True,
          "does_not_estimate_actual_business_capacity":True,
          "allow_inventory_production_without_accepted_orders":True,
          "not_a_closed_loop_make_to_order_model":True}}
    (out/"report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("COMPOSITION",result["status"],"prepared",round(prepared_total,6),
          "backlog_end",round(result["model_backlog_end"],6))
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--case",required=True,choices=["S1","S2","S3"])
    ap.add_argument("--proposal",type=Path,required=True)
    ap.add_argument("--originals",type=Path,required=True)
    ap.add_argument("--scratch",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    run(a.case,a.proposal.read_text(encoding="utf-8"),a.originals,a.scratch,a.out)

if __name__=="__main__":main()
