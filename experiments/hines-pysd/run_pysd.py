#!/usr/bin/env python3
"""Cross-engine parity: original .mdl via PySD versus independent Euler baseline.

A failed import is BLOCKED_TRANSLATION, not mathematical disagreement. Original
.mdl bytes are verified by SHA-256 and kept outside repository and artifacts.
"""
import argparse,csv,hashlib,json,math,platform,traceback
from pathlib import Path
import pysd
from independent_euler import baseline

COLUMNS={
 "delay.mdl":{"Material":"material","Material flowing in":"inflow","Material flowing out":"outflow"},
 "CapUtil.mdl":{"Production":"production","Utilization":"utilization","Indicated Utilization":"indicated_utilization"},
 "invbakf.mdl":{"Inventory":"inventory","Backlog":"backlog","Orders":"orders","Producing":"producing","Shipping":"shipping"},
 "invbakl.mdl":{"Inventory":"inventory","Backlog":"backlog","Orders":"orders","Producing":"producing","Shipping":"shipping"}
}

def one(name,path,spec,out,abs_tol,rel_tol):
    model=pysd.read_vensim(str(path),encoding="UTF-8")
    actual=model.run(return_columns=list(COLUMNS[name]))
    expected=baseline(name,spec)
    at={round(float(t),8):i for i,t in enumerate(actual.index)}
    ex={round(float(r["time"]),8):r for r in expected}
    errors=[];rows=[];maxerr=0.
    for t,x in ex.items():
        if t not in at:
            errors.append({"time":t,"error":"MISSING_TIMESTAMP"});continue
        for original,field in COLUMNS[name].items():
            p=float(actual.iloc[at[t]][original]);q=float(x[field])
            diff=abs(p-q);maxerr=max(maxerr,diff)
            ok=math.isfinite(p) and math.isclose(p,q,abs_tol=abs_tol,rel_tol=rel_tol)
            rows.append(dict(time=t,variable=original,independent_euler=q,
                             pysd=p,absolute_error=diff,within_tolerance=ok))
            if not ok:errors.append({"time":t,"variable":original,"error":diff})
    for t in at.keys()-ex.keys():errors.append({"time":t,"error":"EXTRA_TIMESTAMP"})
    actual.to_csv(out/(name[:-4]+"_pysd.csv"),index_label="time")
    with (out/(name[:-4]+"_diff.csv")).open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["time","variable","independent_euler","pysd","absolute_error","within_tolerance"])
        w.writeheader();w.writerows(rows)
    return {"status":"PASS" if not errors else "MISMATCH",
            "independent_steps":len(expected),"pysd_steps":len(actual.index),
            "num_errors":len(errors),"max_absolute_error":maxerr,"first_errors":errors[:12],
            "compared_variables":list(COLUMNS[name])}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--sources",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    spec=json.loads(Path(__file__).with_name("specifications_extracted.json").read_text())
    results={}
    for name,config in spec["model_provenance"].items():
        src=a.sources/name
        if not src.exists():
            results[name]={"status":"BLOCKED_SOURCE"}
        elif hashlib.sha256(src.read_bytes()).hexdigest()!=config["source_sha256"]:
            results[name]={"status":"BLOCKED_DIGEST"}
        else:
            try:results[name]=one(name,src,spec["models"][name],a.out,1e-6,1e-8)
            except Exception as e:
                results[name]={"status":"BLOCKED_TRANSLATION_OR_EXECUTION",
                               "exception":type(e).__name__,"message":str(e)[:900],
                               "traceback":traceback.format_exc()[-4500:]}
        print("PYSD_PARITY",name,results[name]["status"],flush=True)
    summary={"engine":"pysd","pysd_version":getattr(pysd,"__version__","unknown"),
             "python_version":platform.python_version(),"source":"verified original publisher .mdl",
             "baseline":"independent Euler with source-extracted lookup tables",
             "abs_tol":1e-6,"rel_tol":1e-8,"models":results,
             "overall":"PASS" if all(r["status"]=="PASS" for r in results.values()) else "NOT_VERIFIED"}
    (a.out/"parity_report.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    print("PYSD_PARITY_SUMMARY",json.dumps({"overall":summary["overall"],"models":{k:v["status"] for k,v in results.items()}}),flush=True)
    if summary["overall"]!="PASS":raise SystemExit(1)

if __name__=="__main__":main()
