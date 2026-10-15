#!/usr/bin/env python3
"""M01 structural composition gate, based only on public observations and verified Hines molecules.

No hidden oracle, no LLM, no fitted dynamics. This outputs an *unexecutable*
wiring candidate with traceable evidence and explicitly unresolved ports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOMAINS = {"orders", "meals_equivalent", "MXN"}
WINDOWS = ("valle_am", "pico", "valle_pm")


def canonical(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha(data):
    return hashlib.sha256(canonical(data).encode("utf-8")).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def extract(reference, dotted):
    value = reference
    for segment in dotted.split("."):
        if isinstance(value, dict):
            value = value[segment]
        elif isinstance(value, list):
            value = value[int(segment)]
        else:
            raise ValueError("Invalid reference path: " + dotted)
    if not {"value", "unit", "source_id", "sha256", "evidence_type"}.issubset(value):
        raise ValueError("Not a typed evidence reference: " + dotted)
    return {k: value[k] for k in ("value", "unit", "source_id", "sha256", "evidence_type")}


def check_composition(contract, origins):
    if contract.get("schema_version") != "hines.m01.composition.v0.1":
        raise ValueError("Wrong composition version")
    if contract.get("execution_status") != "STRUCTURE_ONLY_NO_M01_SIMULATION":
        raise ValueError("Structural-only safety flag missing")

    selected = [m for m in contract["molecules"] if m["status"] != "NOT_COMPOSED_ALTERNATIVE"]
    candidates = {m["id"]: m for m in selected}
    if set(candidates) != {"backlog_shipping", "kitchen_capacity", "supplier_pipeline"}:
        raise ValueError("Unexpected active source molecules")
    for component in contract["molecules"]:
        file = component["file"]
        if file not in origins["model_provenance"] or file not in origins["models"]:
            raise ValueError("No verified original for " + file)
        assert len(origins["model_provenance"][file]["source_sha256"]) == 64

    states = {s["id"]: s for s in contract["states"]}
    if len(states) != len(contract["states"]):
        raise ValueError("Duplicate states")
    rates = {r["id"]: r for r in contract["rates"]}
    if len(rates) != len(contract["rates"]):
        raise ValueError("Duplicate rates")
    for s in states.values():
        if s["unit"] not in DOMAINS:
            raise ValueError("Unknown entity unit for state " + s["id"])
    for rate in rates.values():
        if rate["unit"].count("/") != 1:
            raise ValueError("Rate must be entity / time " + rate["id"])
        entity, time = rate["unit"].split("/")
        if entity not in DOMAINS or time not in ("hour", "day"):
            raise ValueError("Rate dimension unknown " + rate["id"])
        for sid in rate["into"] + rate["out_of"]:
            if sid not in states:
                raise ValueError("Dangling rate endpoint " + sid)
            if states[sid]["unit"] != entity:
                raise ValueError("Cross-entity rate " + rate["id"] + " -> " + sid)

    map_backlog = candidates["backlog_shipping"]["bindings"]
    if map_backlog["Inventory"] != "prepared_orders_waiting_dispatch":
        raise ValueError("Hines finished-goods inventory cannot be raw ingredient inventory")
    if map_backlog["Backlog"] != "uncompleted_accepted_orders":
        raise ValueError("Must represent uncompleted accepted order commitments")
    if candidates["supplier_pipeline"]["status"] != "HYPOTHESIS_NOT_EQUATED_WITH_FIXED_LEAD":
        raise ValueError("First-order delay must not be equated with nominal fixed lead time")
    if not any(u["id"] == "meals_per_order" for u in contract["uncertainties"]):
        raise ValueError("Unresolved meals/order conversion must be explicit")
    if any(m["file"] == "invbakl.mdl" for m in selected):
        raise ValueError("Alternative backlog molecule must not be stacked")
    return {"selected_molecules": sorted(candidates), "states_checked": len(states),
            "rates_checked": len(rates), "unresolved_ports": len(contract["uncertainties"])}


def check_observations(public, contract):
    if public.get("case_id") != contract["anchored_case"]:
        raise ValueError("Unexpected case")
    computed_sha = sha(public)
    if computed_sha != contract["expected_public_input_sha256"]:
        raise ValueError("Public M01 evidence hash changed: " + computed_sha)
    if "SINTÉTICO" not in public.get("data_origin", ""):
        raise ValueError("M01 origin was not identified as synthetic")
    if len(public["pos_by_arrival_cohort"]) != 42 or len(public["daily_stocks"]) != 14:
        raise ValueError("Expected 42 POS windows and 14 daily ledgers")
    limitation = public["limitations"]
    if limitation.get("kitchen_stage_trace_available") is not False:
        raise ValueError("Unexpected kitchen trace availability")
    if limitation.get("pickup_stage_trace_available") is not False:
        raise ValueError("Unexpected dispatch trace availability")
    # Do not open generator/holdout: every field in this report is public.
    for x in public["pos_by_arrival_cohort"] + public["daily_stocks"]:
        if x.get("evidence_type") != "OBSERVADO" or len(x.get("sha256", "")) != 64:
            raise ValueError("Observed source row not verified by public preparer")
    return computed_sha


def report(public, contract, origins):
    gate = check_composition(contract, origins)
    input_sha = check_observations(public, contract)
    refs = {name: extract(public, path) for name, path in contract["reference_binding_paths"].items()}
    kitchen = refs["kitchen_nominal_orders_per_hour"]
    dispatch = refs["dispatch_nominal_orders_per_hour"]
    hours = refs["window_hours"]
    if (kitchen["unit"], dispatch["unit"], hours["unit"]) != ("orders/hour", "orders/hour", "hours"):
        raise ValueError("Reference rate/window dimensional mismatch")
    if refs["opening_raw_inventory_meals_equivalent"]["unit"] != "meals_equivalent":
        raise ValueError("Wrong opening raw inventory unit")
    if refs["opening_cash_mxn"]["unit"] != "MXN":
        raise ValueError("Wrong opening cash unit")
    if refs["supplier_nominal_lead_days"]["unit"] != "days":
        raise ValueError("Wrong supplier lead time unit")

    kitchen_per_window = kitchen["value"] * hours["value"]
    dispatch_per_window = dispatch["value"] * hours["value"]
    if kitchen_per_window <= 0 or dispatch_per_window <= 0:
        raise ValueError("Nominal capacities must be positive")

    cohorts = []
    for x in sorted(public["pos_by_arrival_cohort"], key=lambda o:(o["day"], WINDOWS.index(o["window"]))):
        accepted = x["presencial_accepted"] + x["delivery_accepted"]
        completed_service_window = (
            x["presencial_service_window_completed"] + x["delivery_service_window_completed"]
        )
        cohorts.append({
            "day": x["day"], "arrival_window": x["window"],
            "observed_accepted_orders_arrival_cohort": accepted,
            "observed_service_window_completed_orders": completed_service_window,
            "nominal_reference_kitchen_orders_per_window": kitchen_per_window,
            "nominal_reference_dispatch_orders_per_window": dispatch_per_window,
            "arrival_pressure_vs_nominal_kitchen_reference": accepted / kitchen_per_window,
            "arrival_pressure_vs_nominal_dispatch_reference": accepted / dispatch_per_window,
            "arrival_count_above_nominal_kitchen_reference": accepted > kitchen_per_window,
            "source_id": x["source_id"], "sha256": x["sha256"],
            "interpretation": "Intake pressure only. No direct measurement of production, pickup, or actual saturation."
        })

    pressure = {
        "windows": len(cohorts),
        "arrival_windows_above_nominal_kitchen_reference": sum(x["arrival_count_above_nominal_kitchen_reference"] for x in cohorts),
        "maximum_accepted_orders_in_one_arrival_window": max(x["observed_accepted_orders_arrival_cohort"] for x in cohorts),
        "total_accepted_orders": sum(x["observed_accepted_orders_arrival_cohort"] for x in cohorts),
        "total_service_window_completions": sum(x["observed_service_window_completed_orders"] for x in cohorts)
    }
    reasons = [u["blocks"] for u in contract["uncertainties"]]
    return {
        "experiment": "M01_HINES_STRUCTURAL_COMPOSITION_V1",
        "case_id": "M01", "case_origin": public["data_origin"], "public_input_sha256": input_sha,
        "originals_verified_in": "https://github.com/yudocyudoc/short/actions/runs/38808748143",
        "hines_sha256": {m["file"]: origins["model_provenance"][m["file"]]["source_sha256"]
                         for m in contract["molecules"]},
        "structure_gate": {"status":"PASS", **gate},
        "reference_bindings": refs,
        "cohort_screen": pressure,
        "cohort_rows": cohorts,
        "selected_modules": [m for m in contract["molecules"]
                             if m["status"] != "NOT_COMPOSED_ALTERNATIVE"],
        "alternative_module": [m for m in contract["molecules"]
                               if m["status"] == "NOT_COMPOSED_ALTERNATIVE"],
        "observed_initial_state": {
            "raw_ingredient_inventory": refs["opening_raw_inventory_meals_equivalent"],
            "cash": refs["opening_cash_mxn"]
        },
        "unresolved": contract["uncertainties"],
        "simulation_gate": {
            "status": "BLOCKED_NOT_IDENTIFIED",
            "reason": "Composition interfaces are typed, but actual transition rates and boundary conversions are not identified.",
            "blocked_by": reasons,
            "counterfactuals": "FORBIDDEN",
            "calibrated_forecasts": "FORBIDDEN"
        },
        "methodological_warnings": [
            "Hines Inventory in invbakf.mdl is finished order units, not raw meals_equivalent.",
            "A shared Shipping event closes an order commitment and removes a prepared order; do not interpret the sum of two ledgers as a single conserved pool.",
            "Kitchen reference 16 orders/hour and dispatch reference 15 orders/hour are calibrated nominal capacities, not measured virtual effective throughput.",
            "The CapUtil lookup reaches 1.15 of nominal at high demand; nominal capacity is not a strict hard ceiling.",
            "Arrival-cohort completions and service-window completions are different temporal groupings.",
            "Supplier nominal lead of 1 day does not establish exponential delay required by delay.mdl.",
            "No hidden generator, oracle, or aggregate exploratory SD model was read.",
            "This is a structural assembly and observation screen, not an executable cafeteria model."
        ],
        "llm_calls": 0, "pysd_cafeteria_runs": 0
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--contract", type=Path, default=HERE/"m01_composition.json")
    ap.add_argument("--origins", type=Path, default=HERE/"specifications_extracted.json")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    result = report(load(a.input), load(a.contract), load(a.origins))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print("M01_HINES_COMPOSITION", json.dumps({
        "structure": result["structure_gate"]["status"],
        "simulation": result["simulation_gate"]["status"],
        "cohort_windows": result["cohort_screen"]["windows"],
        "arrival_windows_above_nominal_reference": result["cohort_screen"]["arrival_windows_above_nominal_kitchen_reference"],
        "llm_calls": result["llm_calls"], "pysd_cafeteria_runs": result["pysd_cafeteria_runs"]
    }))


if __name__ == "__main__":
    main()
