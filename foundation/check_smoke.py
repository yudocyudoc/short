#!/usr/bin/env python3
"""E0 engineering regression for pre-existing molecules; no causal score."""
import argparse
import csv
import json
import math
from pathlib import Path

PHYSICAL = ("acceptedRate", "physicalDeliveryRate", "waitingStock", "totalDelivered")
EPS = 1e-6


def column(row, name):
    matches = [value for key, value in row.items() if key == name or key.endswith("." + name)]
    if len(matches) != 1:
        raise ValueError("MISSING_OR_AMBIGUOUS_COLUMN:" + name)
    return float(matches[0])


def read_series(file):
    with Path(file).open(newline="", encoding="utf-8-sig") as handle:
        data = list(csv.DictReader(handle))
    if len(data) < 10:
        raise ValueError("TOO_FEW_ROWS:" + str(file))
    previous_time = -math.inf
    unique = []
    for row in data:
        t = column(row, "time")
        if not math.isfinite(t) or t + 1e-10 < previous_time:
            raise ValueError("BAD_TIME_ORDER")
        previous_time = t
        fields = ["time", *PHYSICAL, "reportedDeliveryRate"]
        if not all(math.isfinite(column(row, k)) for k in fields):
            raise ValueError("NON_FINITE_SERIES")
        if unique and abs(column(unique[-1], "time") - t) <= 1e-10:
            unique[-1] = row   # keep post-event sample, never average event boundaries
        else:
            unique.append(row)
    return unique


def verify(direct, filtered):
    a, b = read_series(direct), read_series(filtered)
    if len(a) != len(b):
        raise ValueError("UNEQUAL_SAMPLE_COUNTS")
    if not 0.01 <= max(column(x, "physicalDeliveryRate") for x in a):
        raise ValueError("NO_PHYSICAL_ACTIVITY")
    if column(a[-1], "totalDelivered") <= 0:
        raise ValueError("NO_DELIVERIES")
    physical_delta = 0
    report_effect = 0
    direct_delta = 0
    for idx, (left, right) in enumerate(zip(a, b)):
        if abs(column(left, "time") - column(right, "time")) > 1e-9:
            raise ValueError("TIME_GRIDS_DIFFER")
        for series in (left, right):
            if column(series, "waitingStock") < -EPS:
                raise ValueError("NEGATIVE_STOCK")
            if column(series, "totalDelivered") < -EPS:
                raise ValueError("NEGATIVE_DELIVERIES")
            if column(series, "physicalDeliveryRate") < -EPS:
                raise ValueError("NEGATIVE_PHYSICAL_FLOW")
            if column(series, "physicalDeliveryRate") > 5 + EPS:
                raise ValueError("THROUGHPUT_CAP_EXCEEDED")
        if idx:
            if column(left, "totalDelivered") + EPS < column(a[idx-1], "totalDelivered"):
                raise ValueError("NONMONOTONE_DELIVERIES")
        for name in PHYSICAL:
            physical_delta = max(physical_delta, abs(column(left, name) - column(right, name)))
        direct_delta = max(direct_delta, abs(column(left, "physicalDeliveryRate") - column(left, "reportedDeliveryRate")))
        report_effect = max(report_effect, abs(column(right, "physicalDeliveryRate") - column(right, "reportedDeliveryRate")))
    if physical_delta > EPS:
        raise ValueError("REPORT_FILTER_CHANGED_PHYSICAL_SYSTEM")
    if direct_delta > EPS:
        raise ValueError("DIRECT_REPORT_NOT_DIRECT")
    if report_effect <= 0.001:
        raise ValueError("FILTER_NO_MEASURABLE_EFFECT")
    return {
        "technical": "PASS",
        "methodological": "ENGINEERING_ONLY",
        "world_identification": "NOT_RUN",
        "graph_composition": "NOT_RUN",
        "n_common_time_samples": len(a),
        "max_physical_delta": physical_delta,
        "max_direct_report_delta": direct_delta,
        "max_filter_report_delta": report_effect,
        "note": "Fixture is explicitly known and cannot validate search, interpretation, or identifiability."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.directory / "direct_res.csv", args.directory / "filtered_res.csv")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("IGC_V3_FOUNDATION_SMOKE " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
