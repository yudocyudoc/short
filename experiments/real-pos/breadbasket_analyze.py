#!/usr/bin/env python3
"""Reproducible observational POS summary: BreadBasket_DMS original Kaggle mirror.

No LLM, no queue estimation, no throughput/capacity estimation. It strictly
counts completed/recorded transactions and item rows per time interval.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,statistics
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path

SOURCE_COMMIT="8415fd4eedd124d739d75430853796e13ded1009"
SOURCE_BLOB="ceea9513b75a3dda41a9209b6fd1875c12580933"
SOURCE_REPO="prasertcbs/basic-dataset"
SOURCE_PATH="BreadBasket_DMS.csv"
SOURCE_URL=f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/{SOURCE_PATH}"
EXPECTED={"raw_item_rows":21293,"none_rows":786,"non_none_item_rows":20507,
          "raw_transaction_ids":9531,"valid_transactions":9465,
          "none_only_transaction_ids":66,"distinct_products":94}
EXPECTED_COLUMNS=("Date","Time","Transaction","Item")

def digest(raw: bytes):
    content_blob=b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw
    return {"sha256":hashlib.sha256(raw).hexdigest(),
            "git_blob_sha1":hashlib.sha1(content_blob).hexdigest(),
            "source_bytes":len(raw)}

def build(raw: bytes, strict: bool=True):
    check=digest(raw)
    if strict and check["git_blob_sha1"]!=SOURCE_BLOB:
        raise ValueError("SOURCE_BLOB_MISMATCH: refusing unverified POS bytes")
    decoded=raw.decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(decoded))
    if tuple(reader.fieldnames or ())!=EXPECTED_COLUMNS:
        raise ValueError("BAD_COLUMNS: expected exact raw POS schema")
    raw_rows=0; none_rows=0; all_ids=set(); order_data={}
    item_counter=Counter(); item_dates=Counter()
    transaction_item_count=Counter()
    for idx,rec in enumerate(reader,1):
        raw_rows+=1
        trx=rec["Transaction"].strip()
        if not trx or not trx.isdigit():
            raise ValueError(f"INVALID_TRANSACTION_ID at row {idx}")
        try:
            stamp=datetime.strptime(rec["Date"].strip()+" "+rec["Time"].strip(),"%Y-%m-%d %H:%M:%S")
        except ValueError as err:
            raise ValueError(f"INVALID_TIMESTAMP at row {idx}: {err}") from err
        item=rec["Item"].strip()
        if not item:
            raise ValueError(f"EMPTY_ITEM at row {idx}")
        all_ids.add(trx)
        if item.upper()=="NONE":
            none_rows+=1
            continue
        # Multiple purchased items in one transaction are NOT distinct customers/orders.
        previous=order_data.setdefault(trx,stamp)
        if previous!=stamp:
            raise ValueError(f"INCONSISTENT_TRANSACTION_TIMESTAMP for ID {trx}")
        item_counter[item]+=1
        item_dates[stamp.date().isoformat()]+=1
        transaction_item_count[trx]+=1
    tx_hour=Counter(); tx_quarter=Counter(); day_count=Counter()
    dow_hour=Counter(); dow_quarter=Counter(); dow_count=Counter()
    for stamp in order_data.values():
        day=stamp.date().isoformat();hour=stamp.hour;quarter=15*(stamp.minute//15)
        tx_hour[(day,hour)]+=1
        tx_quarter[(day,hour,quarter)]+=1
        day_count[day]+=1
        dow_count[stamp.weekday()]+=1
        dow_hour[(stamp.weekday(),hour)]+=1
        dow_quarter[(stamp.weekday(),hour,quarter)]+=1
    max_hour=max(tx_hour.values()) if tx_hour else 0
    max_quarter=max(tx_quarter.values()) if tx_quarter else 0
    high_hour=sorted([{"date":d,"hour":h,"transactions":c}
                      for (d,h),c in tx_hour.items() if c==max_hour],
                     key=lambda x:(x["date"],x["hour"]))
    high_quarter=sorted([{"date":d,"hour":h,"start_minute":q,"transactions":c}
                         for (d,h,q),c in tx_quarter.items() if c==max_quarter],
                        key=lambda x:(x["date"],x["hour"],x["start_minute"]))
    stats={"raw_item_rows":raw_rows,"none_rows":none_rows,
           "non_none_item_rows":sum(item_counter.values()),
           "raw_transaction_ids":len(all_ids),"valid_transactions":len(order_data),
           "none_only_transaction_ids":len(all_ids)-len(order_data),
           "distinct_products":len(item_counter)}
    if strict and stats!=EXPECTED:
        raise ValueError("SOURCE_RECORD_COUNTS_CHANGED: "+json.dumps(stats,sort_keys=True))
    if sum(day_count.values())!=len(order_data):
        raise AssertionError("Transaction conservation failed")
    if sum(transaction_item_count.values())!=sum(item_counter.values()):
        raise AssertionError("Item-row conservation failed")
    span={"min_sale_timestamp":min(order_data.values()).isoformat() if order_data else None,
          "max_sale_timestamp":max(order_data.values()).isoformat() if order_data else None,
          "calendar_days_with_recorded_sales":len(day_count)}
    def ordered_counter(counter,labels):
        return [{**dict(zip(labels,key)), "count":n}
                for key,n in sorted(counter.items())]
    report={
        "experiment":"BREAD_BASKET_OBSERVED_POS_V1",
        "source":{
            "status":"PUBLIC_SECONDARY_MIRROR","attributed_business":"The Bread Basket, Edinburgh",
            "attribution_not_independently_audited":True,
            "original_dataset":"https://www.kaggle.com/datasets/mittalvasu95/the-bread-basket",
            "mirror_repository":SOURCE_REPO,"mirror_commit":SOURCE_COMMIT,
            "raw_path":SOURCE_PATH,"source_url":SOURCE_URL, **check,
            "rights":"Original dataset license not independently verified; original records not republished"
        },
        "schema":{"source_columns":list(EXPECTED_COLUMNS),
                  "event":"registered_sale_transaction_timestamp",
                  "time_precision":"seconds",
                  "transaction_unit":"unique Transaction ID with at least one non-NONE item",
                  "item_unit":"one non-NONE raw item row; duplicates within a transaction retained",
                  "null_item_policy":"exclude NONE product rows; preserve count",
                  "no_imputation":True},
        "quality":{"counts":stats,**span,
                   "invalid_timestamp_rows":0,"inconsistent_transaction_clock_rows":0},
        "observed_patterns":{
            "busiest_observed_hour":high_hour,
            "busiest_observed_quarter_hour":high_quarter,
            "max_transactions_in_observed_hour":max_hour,
            "max_transactions_in_observed_15min":max_quarter,
            "transactions_by_weekday":[{"weekday_monday_zero":i,"count":dow_count[i]} for i in range(7)],
            "transaction_counts_by_day":[{"date":d,"count":n} for d,n in sorted(day_count.items())],
            "transaction_counts_by_observed_hour":ordered_counter(tx_hour,("date","hour")),
            "transaction_counts_by_observed_15min":ordered_counter(tx_quarter,("date","hour","start_minute")),
            "transactions_by_weekday_hour":ordered_counter(dow_hour,("weekday_monday_zero","hour")),
            "top_product_rows":[{"item":k,"rows":v} for k,v in item_counter.most_common(15)],
            "total_sale_transactions":len(order_data)
        },
        "identifiability":{
            "observable":["registered sales events by time","items recorded per transaction",
                          "day-of-week and intraday variation of completed/registered sales"],
            "not_observable":["unserved customer demand","actual customer arrival time",
                              "preparation start/end","queue lengths","service time",
                              "kitchen or dispatch capacity","stock levels/recipe consumption",
                              "delivery channel","provider replenishment","competition/zonal population"],
            "sd_use":"EXOGENOUS_OBSERVED_SALES_PATTERN_ONLY",
            "stock_flow_calibration":"BLOCKED_UNTIL_INDEPENDENT_OBSERVATIONS",
            "warnings":[
              "Recorded POS timestamps are NOT necessarily customer arrivals.",
              "Observed sales counts cannot distinguish suppressed demand from low demand.",
              "No sales in a slot cannot be equated with zero demand or with being open.",
              "Sampled 15-minute maxima are historical registered sales, not maximum service capacity.",
              "Item-row count 20507 cannot be used as count of unique orders 9465.",
              "This dataset cannot validate a claim about an inventory leakage or its cause."
            ]
        },
        "llm_calls":0,"sd_model_fitted":False,"queue_inferred":False
    }
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--csv",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    report=build(args.csv.read_bytes())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("BREAD_BASKET_AUDIT",json.dumps({
        "counts":report["quality"]["counts"],
        "period":report["quality"]["min_sale_timestamp"]+" to "+report["quality"]["max_sale_timestamp"],
        "max_observed_hour":report["observed_patterns"]["max_transactions_in_observed_hour"],
        "max_observed_15min":report["observed_patterns"]["max_transactions_in_observed_15min"],
        "sd_calibration":report["identifiability"]["stock_flow_calibration"],
        "llm_calls":report["llm_calls"]
    },sort_keys=True))

if __name__=="__main__":
    main()
