#!/usr/bin/env python3
"""Conditional SD demo using original Hines functions and real *recorded sales* timing.

PySD executes (1) Hines Capacity Utilization and (2) Hines Backlog Shipping
Protected by Flow. These are two linked original structures, not a calibrated
or empirically validated bakery model.

The original publisher .mdl files MUST pass the frozen SHA-256 verification
before running. Their unit labels are adjusted only in disposable .mdl files
to reflect the explicit hours/orders scenario clock; equations and lookup
points stay unaltered. Never commit or upload original/temporary .mdl copies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import pandas as pd
import pysd


ROOT = Path(__file__).resolve().parent
SOURCE_MANIFEST = ROOT.parents[2] / "hines-pysd" / "specifications_extracted.json"


def jsonfile(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evidence_bins(aggregates, day: str):
    if aggregates["experiment"] != "BREAD_BASKET_OBSERVED_POS_V1":
        raise ValueError("Wrong POS aggregate provenance")
    if aggregates["source"]["git_blob_sha1"] != "ceea9513b75a3dda41a9209b6fd1875c12580933":
        raise ValueError("POS source blob mismatch")
    count = Counter()
    for row in aggregates["observed_patterns"]["transaction_counts_by_observed_15min"]:
        if row["date"] != day:
            continue
        if row["start_minute"] not in (0,15,30,45):
            raise ValueError("Non-quarter-hour source aggregate")
        bin_i = row["hour"] * 4 + row["start_minute"] // 15
        if bin_i < 0 or bin_i >= 96:
            raise ValueError("Non-day source window")
        count[bin_i] += row["count"]
    counts = [count[i] for i in range(96)]
    day_totals = {row["date"]:row["count"] for row in aggregates["observed_patterns"]["transaction_counts_by_day"]}
    if day not in day_totals or sum(counts) != day_totals[day]:
        raise ValueError("Quarter-hour observed total mismatch with day tally")
    return counts


def ephemeral_units(name: str, original: Path, expected_sha256: str, dest: Path):
    raw = original.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != expected_sha256:
        raise ValueError("Verified original Hines digest mismatch: " + name)
    if not raw.startswith(b"{UTF-8}"):
        raise ValueError("Unrecognized original Vensim format")
    data = raw.decode("utf-8", errors="strict")
    # Unit relabeling only. All original Hines equations, lookup coordinates,
    # and structure/flow logic are preserved for PySD.
    if name == "CapUtil.mdl":
        assert "Widgets/Week" in data and "Week" in data
        derived = data.replace("Widgets", "orders").replace("Week", "Hour")
    elif name == "invbakf.mdl":
        assert "Widgets/Month" in data and "Month" in data
        derived = data.replace("Widgets", "orders").replace("Month", "Hour")
    else:
        raise ValueError("Unexpected molecule")
    path = dest / name
    path.write_text(derived, encoding="utf-8")
    return path, {
        "publisher_original_sha256": sha,
        "original_name": name,
        "ephemeral_relabelled_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "unit_relabelling_only": True,
        "model_formulas_changed": False,
        "transient_models_persisted": False,
    }


def series_from_counts(counts):
    # Model Euler steps are exactly on 15-minute knots. PySD accepts a series
    # and linearly interpolates between knots; this interpolation does not
    # change samples at these integration boundaries. Use 0 at t=24 for the
    # end-of-day state; it is not integrated as a new 15-minute interval.
    rates = [4.0 * n for n in counts] + [0.0]
    stamps = [i / 4.0 for i in range(97)]
    return pd.Series(rates,index=stamps,dtype="float64")


def run_one(caputil_file, backlog_file, counts, cap, config):
    dt=float(config["clock"]["dt_hours"])
    if dt!=0.25 or len(counts)!=96:
        raise ValueError("Expected 96 quarter-hour bins")
    t = [i*dt for i in range(97)]
    params=config["scenario_parameters"]
    forcing=series_from_counts(counts)

    # Hines CapUtil.mdl: Production = Capacity * Utilization f(Desired/Capacity)
    capacity_model=pysd.read_vensim(str(caputil_file))
    kitchen = capacity_model.run(
        params={"Capacity":float(cap),"Desired Production":forcing},
        initial_condition="original",time_step=dt,final_time=24.0,saveper=dt,
        return_timestamps=t,
        return_columns=["Desired Production","Capacity","Production","Utilization"]
    )
    if len(kitchen)!=97:
        raise ValueError("Capacity-model result length mismatch")
    kitchen_production=[float(v) for v in kitchen["Production"]]

    # Hines invbakf.mdl: two levels, Backlog and Inventory, regulated Shipping.
    # New no-backlog/no-prepared-stock initial condition is an EXPLICIT
    # counterfactual assumption (not the original 1000 / 2000 widgets).
    order_model=pysd.read_vensim(str(backlog_file))
    result=order_model.run(
        params={
            "Orders":forcing,
            "Producing":pd.Series(kitchen_production,index=t),
            "minimum time to ship":float(params["assumed_minimum_ship_time_hours"]),
            "Time To Process And Ship Order":float(params["assumed_processing_and_shipping_target_hours"])
        },
        initial_condition=(0.0,{"Backlog":float(params["assumed_initial_unfulfilled_orders"]),
                                "Inventory":float(params["assumed_initial_prepared_orders"])}),
        time_step=dt,final_time=24.0,saveper=dt,return_timestamps=t,
        return_columns=["Backlog","Inventory","Orders","Producing","Shipping","Maximum shipping"]
    )
    if len(result)!=97:
        raise ValueError("Backlog-model result length mismatch")

    records=[]
    for i in range(97):
        r=result.iloc[i]
        records.append({
            "time_hours":t[i],
            "observed_sale_transactions_in_bin":counts[i] if i<96 else None,
            "sale_proxy_input_orders_per_hour":float(r["Orders"]),
            "hypothetical_nominal_kitchen_capacity_orders_per_hour":cap,
            "simulated_kitchen_production_orders_per_hour":kitchen_production[i],
            "simulated_shipping_orders_per_hour":float(r["Shipping"]),
            "simulated_unfulfilled_orders":float(r["Backlog"]),
            "simulated_prepared_orders":float(r["Inventory"])
        })
    if any(not math.isfinite(x) for rec in records for x in
           (rec["sale_proxy_input_orders_per_hour"],
            rec["simulated_kitchen_production_orders_per_hour"],
            rec["simulated_shipping_orders_per_hour"],
            rec["simulated_unfulfilled_orders"],
            rec["simulated_prepared_orders"])):
        raise ValueError("Nonfinite model result")
    if min(rec["simulated_unfulfilled_orders"] for rec in records)<-1e-7:
        raise ValueError("Negative backlog in conditional model")
    if min(rec["simulated_prepared_orders"] for rec in records)<-1e-7:
        raise ValueError("Negative prepared stock in conditional model")

    accepted_proxy=sum(counts)
    input_integrated=sum(rec["sale_proxy_input_orders_per_hour"]*dt for rec in records[:-1])
    produced_integrated=sum(rec["simulated_kitchen_production_orders_per_hour"]*dt for rec in records[:-1])
    shipped_integrated=sum(rec["simulated_shipping_orders_per_hour"]*dt for rec in records[:-1])
    backlog_final=records[-1]["simulated_unfulfilled_orders"]
    finished_stock_final=records[-1]["simulated_prepared_orders"]
    b0=params["assumed_initial_unfulfilled_orders"]
    i0=params["assumed_initial_prepared_orders"]
    order_balance_err=backlog_final-(b0+input_integrated-shipped_integrated)
    inventory_balance_err=finished_stock_final-(i0+produced_integrated-shipped_integrated)
    if abs(input_integrated-accepted_proxy)>1e-8:
        raise ValueError("Recorded-sales proxy loss during integration")
    if max(abs(order_balance_err),abs(inventory_balance_err))>1e-6:
        raise ValueError("Conservation failed")

    summary={
        "hypothetical_nominal_kitchen_capacity_orders_per_hour":cap,
        "original_registered_sale_transactions_on_day":accepted_proxy,
        "proxy_orders_integrated":input_integrated,
        "simulated_produced_orders_integrated":produced_integrated,
        "simulated_shipped_orders_integrated":shipped_integrated,
        "simulated_backlog_end_of_day_orders":backlog_final,
        "simulated_maximum_backlog_orders":max(rec["simulated_unfulfilled_orders"] for rec in records),
        "simulated_prepared_inventory_end_of_day_orders":finished_stock_final,
        "simulated_maximum_prepared_inventory_orders":max(rec["simulated_prepared_orders"] for rec in records),
        "conservation_order_abs_error":abs(order_balance_err),
        "conservation_prepared_inventory_abs_error":abs(inventory_balance_err),
        "simulated_conclusion_not_real_diagnosis":True
    }
    return summary, records


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--aggregates",type=Path,required=True)
    parser.add_argument("--originals",type=Path,required=True)
    parser.add_argument("--temporary-models",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    opts=parser.parse_args()
    cfg=jsonfile(ROOT/"scenario_config.json")
    origins=jsonfile(SOURCE_MANIFEST)
    observed=jsonfile(opts.aggregates)
    opts.temporary_models.mkdir(parents=True,exist_ok=True)
    opts.out.mkdir(parents=True,exist_ok=True)
    model_files={};adaptations={}
    for name in cfg["provenance"]["hines_original_models"]:
        source=opts.originals/name
        if not source.is_file():
            raise ValueError("Verified original not downloaded " + name)
        model_files[name],adaptations[name]=ephemeral_units(
            name,source,origins["model_provenance"][name]["source_sha256"],
            opts.temporary_models
        )
    days=[]; combined=[]
    for selected in cfg["preselected_dates"]:
        day=selected["date"]
        counts=evidence_bins(observed,day)
        cases=[]
        for cap in cfg["scenario_parameters"]["hypothetical_kitchen_nominal_capacities_orders_per_hour"]:
            summary,rows=run_one(model_files["CapUtil.mdl"],model_files["invbakf.mdl"],counts,float(cap),cfg)
            cases.append(summary)
            for row in rows:
                combined.append({"date":day,"capacity_scenario_orders_per_hour":cap,**row})
        days.append({
            "date":day,"selection_rule":selected["selection_rule"],
            "source_sale_transactions":sum(counts),
            "nonzero_sale_proxy_15_min_bins":sum(x>0 for x in counts),
            "max_observed_sales_15_min":max(counts),
            "scenarios":cases
        })
    with (opts.out/"conditional_timeseries.csv").open("w",newline="",encoding="utf-8") as fh:
        import csv
        writer=csv.DictWriter(fh,fieldnames=list(combined[0]))
        writer.writeheader();writer.writerows(combined)
    report={
        "experiment":"BREADBASKET_HINES_PYSD_CONDITIONAL_V1",
        "verdict":"SCENARIO_SIMULATION_NOT_EMPIRICAL_VALIDATION",
        "observed_source_git_blob_sha1":observed["source"]["git_blob_sha1"],
        "observed_source_sha256":observed["source"]["sha256"],
        "source_data":"registered sales timestamps only",
        "hines_originals_sha256":{n:origins["model_provenance"][n]["source_sha256"] for n in adaptations},
        "transient_unit_adaptations":adaptations,
        "engine":"PySD",
        "engine_version":pysd.__version__,
        "structural_composition":"two Hines molecules run sequentially; capacity output fed into backlog",
        "no_endogenous_feedback_from_backlog_to_kitchen":True,
        "predeclared_config":cfg,
        "days":days,
        "safety_conclusions":{
            "capacities_are_hypothetical":True,
            "queue_lengths_are_simulated_not_observed":True,
            "observed_transaction_times_are_not_customer_arrival_times":True,
            "observed_sales_are_not_total_demand":True,
            "no_real_bakery_capacity_calibrated":True,
            "no_inventory_or_profit_claims":True,
            "llm_calls":0
        }
    }
    path=opts.out/"conditional_scenario_summary.json"
    path.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("BREADBASKET_HINES_SD",json.dumps({
        "verdict":report["verdict"],
        "engine":report["engine_version"],
        "days":[{"date":d["date"],"registered_sales":d["source_sale_transactions"],
                 "capacity_end_backlog":[[s["hypothetical_nominal_kitchen_capacity_orders_per_hour"],
                                          round(s["simulated_backlog_end_of_day_orders"],5)]
                                         for s in d["scenarios"]]} for d in days],
        "simulations":len(days)*len(cfg["scenario_parameters"]["hypothetical_kitchen_nominal_capacities_orders_per_hour"]),
        "llm_calls":0
    },sort_keys=True))

if __name__=="__main__":
    main()
