#!/usr/bin/env python3
"""C3 deterministic validator. Independent of inference; never repairs the answer.

USAGE: python3 scripts/c3_validator.py path/to/answer.json experiments/c3/evaluation/facts.json
Checks internal balances + declared facts. Not evidence of causal correctness.
"""
import json
from pathlib import Path
import sys

GATES = [
    "G1_JSON", "G2_STOCKS", "G3_FLOW_TYPES", "G4_REQUEST_PATHS",
    "G5_REQUEST_TOTALS", "G6_PENDING_BALANCE", "G7_MATERIAL_BALANCE",
    "G8_CAPACITY", "G9_CROSS_DOMAIN", "G10_EPISTEMIC",
]
STOCK_TYPES = {"inventory": "beverage_equivalent", "accepted_pending": "request"}
FLOW_UNITS = {"request": "request", "material": "beverage_equivalent"}
REQUIRED = {"horizon_hours", "stocks", "flows", "capacity", "feedback", "unknowns"}
CAPACITY_KEYS = {
    "machine_per_hour", "machine_period_max", "material_period_max",
    "joint_period_max", "observed_prepared",
}


def nonnegative_int(value):
    return type(value) is int and value >= 0


def validate(payload, facts):
    """Return deterministic gate scores and compact errors, no corrections."""
    gates = {name: False for name in GATES}
    why = {}

    def check(name, valid, reason):
        gates[name] = bool(valid)
        if not valid:
            why[name] = reason

    if not isinstance(payload, dict) or set(payload) != REQUIRED:
        check("G1_JSON", False, "One JSON object with exactly the six required top-level keys")
        return report(gates, why)
    stocks = payload["stocks"]
    flows = payload["flows"]
    capacity = payload["capacity"]
    feedback = payload["feedback"]
    unknowns = payload["unknowns"]
    valid_stocks = isinstance(stocks, list) and all(
        isinstance(s, dict) and set(s) == {"id", "unit", "initial", "final"}
        and isinstance(s["id"], str) and isinstance(s["unit"], str)
        and nonnegative_int(s["initial"]) and nonnegative_int(s["final"])
        for s in stocks
    )
    valid_flows = isinstance(flows, list) and all(
        isinstance(t, dict) and set(t) == {"id", "entity", "from", "to", "total", "unit"}
        and all(isinstance(t[k], str) and bool(t[k]) for k in ["id", "entity", "from", "to", "unit"])
        and nonnegative_int(t["total"])
        for t in flows
    )
    valid_capacity = isinstance(capacity, dict) and set(capacity) == CAPACITY_KEYS and all(
        nonnegative_int(v) for v in capacity.values()
    )
    valid_feedback = isinstance(feedback, list) and all(
        isinstance(f, dict) and set(f) == {"name", "status", "justification"}
        and all(isinstance(f[k], str) for k in f)
        for f in feedback
    )
    valid_unknowns = isinstance(unknowns, list) and all(isinstance(u, str) for u in unknowns)
    check("G1_JSON", nonnegative_int(payload["horizon_hours"]) and valid_stocks and
          valid_flows and valid_capacity and valid_feedback and valid_unknowns,
          "Required field type, list element, total or unit malformed")
    if not gates["G1_JSON"]:
        return report(gates, why)

    by_stock = {s["id"]: s for s in stocks}
    check("G2_STOCKS",
          len(stocks) == len(STOCK_TYPES) and len(by_stock) == len(stocks)
          and all(k in by_stock and by_stock[k]["unit"] == unit for k, unit in STOCK_TYPES.items())
          and by_stock.get("inventory", {}).get("initial") == facts["initial_inventory"]
          and by_stock.get("accepted_pending", {}).get("initial") == facts["initial_pending"],
          "Need exactly inventory and accepted_pending with correct units and starting stocks")

    ids = [t["id"] for t in flows]
    correct_types = all(t["entity"] in FLOW_UNITS and t["unit"] == FLOW_UNITS.get(t["entity"])
                        for t in flows)
    req_edges = [(t["from"], t["to"]) for t in flows if t["entity"] == "request"]
    mat_edges = [(t["from"], t["to"]) for t in flows if t["entity"] == "material"]
    allowed_req = [tuple(edge) for edge in facts["allowed_request_edges"]]
    allowed_mat = [tuple(edge) for edge in facts["allowed_material_edges"]]
    check("G3_FLOW_TYPES",
          len(flows) == 6 and len(set(ids)) == len(ids) and correct_types
          and all(edge in allowed_req for edge in req_edges)
          and all(edge in allowed_mat for edge in mat_edges),
          "Only unique unit-consistent request/material flows on allowed routes")
    check("G4_REQUEST_PATHS",
          len(req_edges) == len(allowed_req) and
          len(set(req_edges)) == len(req_edges) and set(req_edges) == set(allowed_req),
          "Required request transitions missing, duplicated or wrongly directed")

    request_by_edge = {(t["from"], t["to"]): t["total"] for t in flows if t["entity"] == "request"}
    material_by_edge = {(t["from"], t["to"]): t["total"] for t in flows if t["entity"] == "material"}
    received = request_by_edge.get(("external", "submitted"))
    accepted = request_by_edge.get(("submitted", "accepted_pending"))
    rejected = request_by_edge.get(("submitted", "rejected"))
    canceled = request_by_edge.get(("accepted_pending", "canceled"))
    fulfilled = request_by_edge.get(("accepted_pending", "fulfilled"))
    consumed = material_by_edge.get(("inventory", "consumed"))
    expected_accepted = facts["requests_total"] - facts["rejected_before_acceptance"]
    check("G5_REQUEST_TOTALS",
          received == facts["requests_total"] and rejected == facts["rejected_before_acceptance"]
          and accepted == expected_accepted and canceled == facts["canceled_after_acceptance"]
          and fulfilled == facts["prepared_delivered"] and
          received == accepted + rejected,
          "Request period totals or submitted partition conflict with observations")
    pending_expected = facts["initial_pending"] + expected_accepted - facts["canceled_after_acceptance"] - facts["prepared_delivered"]
    check("G6_PENDING_BALANCE",
          gates["G2_STOCKS"] and all(v is not None for v in (accepted, canceled, fulfilled))
          and by_stock["accepted_pending"]["final"] == facts["initial_pending"] + accepted - canceled - fulfilled
          and by_stock["accepted_pending"]["final"] == pending_expected,
          "Accepted-pending closing stock does not match accepted minus canceled/fulfilled")

    inventory_expected = facts["initial_inventory"] + facts["replenishment"] - facts["other_material_outflows"] - facts["prepared_delivered"]
    check("G7_MATERIAL_BALANCE",
          gates["G2_STOCKS"] and consumed == facts["prepared_delivered"]
          and by_stock["inventory"]["final"] == inventory_expected,
          "Inventory closing stock/consumption contradicts material balance")
    horizon = facts["horizon_hours"]
    machine_max = horizon * facts["machine_capacity_per_hour"]
    material_max = facts["initial_inventory"] + facts["replenishment"]
    check("G8_CAPACITY",
          payload["horizon_hours"] == horizon
          and capacity["machine_per_hour"] == facts["machine_capacity_per_hour"]
          and capacity["machine_period_max"] == machine_max
          and capacity["material_period_max"] == material_max
          and capacity["joint_period_max"] == min(machine_max, material_max)
          and capacity["observed_prepared"] == facts["prepared_delivered"],
          "Capacity or observed production value inconsistent with input/horizon")
    check("G9_CROSS_DOMAIN",
          gates["G3_FLOW_TYPES"] and gates["G4_REQUEST_PATHS"]
          and len(mat_edges) == 1 and set(mat_edges) == set(allowed_mat)
          and consumed == fulfilled and consumed == capacity["observed_prepared"]
          and "prepared_stock" not in by_stock,
          "Material consumed and accepted requests completed disagree or fictitious ready stock")
    check("G10_EPISTEMIC",
          bool(unknowns) and all(u.strip() for u in unknowns)
          and all(f["status"] == "hypothesis" and f["name"].strip() and f["justification"].strip()
                  for f in feedback),
          "Missing uncertainty or declared an observed feedback loop without evidence")
    return report(gates, why)


def report(gates, why):
    score = sum(gates.values())
    return {"status": "ACCEPT" if score == len(GATES) else "REJECT",
            "score": score, "maximum": len(GATES),
            "gates": [{"id": name, "pass": gates[name], "reason": why.get(name)} for name in GATES]}


def load_and_validate(raw_text, facts):
    try:
        payload = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        return report({g: False for g in GATES},
                      {"G1_JSON": "Response is not exactly one JSON object; no repair attempted"})
    return validate(payload, facts)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python3 scripts/c3_validator.py MODEL_OUTPUT.json facts.json")
    outcome = load_and_validate(Path(sys.argv[1]).read_text(encoding="utf-8"),
                                json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")))
    print(json.dumps(outcome, indent=2, ensure_ascii=False))
    raise SystemExit(0 if outcome["status"] == "ACCEPT" else 1)
