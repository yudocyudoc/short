#!/usr/bin/env python3
"""Compare a real PySD run of the pinned Hines models with two OpenModelica runs.

Strict pointwise comparisons at all 33 quarter-hour timestamps. No interpolation
or endpoint-only judgment; outputs are numerical hypotheses, never measured KPIs.
"""
import argparse,csv,json,math,hashlib
from pathlib import Path

FIELDS={
    "backlog":"model_backlog_orders",
    "inventory":"model_finished_stock_orders",
    "production":"model_production_per_hour",
    "shipping":"model_shipping_per_hour",
}

def read_csv(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=33:raise ValueError(f"EXPECTED_33_TIMEPOINTS:{path}:{len(rows)}")
    return rows

def get(row,key,modelica):
    if modelica:
        # OMC generally exports the unqualified public base-model names;
        # an unambiguous qualified variant is also accepted.
        if key in row:return float(row[key])
        candidates=[v for k,v in row.items() if k.endswith("."+key)]
        if len(candidates)==1:return float(candidates[0])
        raise ValueError(f"MISSING_OR_AMBIGUOUS_OMC_FIELD:{key}:{sorted(row)}")
    return float(row[FIELDS[key]])

def compare(reference,actual,label,tol):
    diffs={}
    if len(reference)!=len(actual):raise ValueError("ROW_MISMATCH")
    for i,(a,b) in enumerate(zip(reference,actual)):
        rt=float(a["time_hours"]);ot=float(b.get("time",b.get("Time","nan")))
        if not math.isclose(rt,ot,rel_tol=0,abs_tol=1e-8):
            raise ValueError(f"TIME_MISMATCH:{label}:{i}:{rt}:{ot}")
    for key in FIELDS:
        errors=[]
        for i,(a,b) in enumerate(zip(reference,actual)):
            x=get(a,key,False);y=get(b,key,True)
            if not math.isfinite(x) or not math.isfinite(y):
                raise ValueError(f"NONFINITE:{label}:{key}:{i}")
            errors.append(abs(x-y))
        diffs[key]={"max_abs_error":max(errors),"max_error_step":errors.index(max(errors)),
                    "within_tolerance":max(errors)<=tol}
    return {"label":label,"fields":diffs,
            "all_points_within_tolerance":all(d["within_tolerance"] for d in diffs.values())}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pysd",type=Path,required=True)
    p.add_argument("--equations",type=Path,required=True)
    p.add_argument("--components",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--tol",type=float,default=1e-4)
    a=p.parse_args()
    if a.tol<=0:raise ValueError("NON_POSITIVE_TOLERANCE")
    py,eq,comp=(read_csv(x) for x in (a.pysd,a.equations,a.components))
    results=[compare(py,eq,"OMC_EQUATIONS_VS_HINES_PYSD",a.tol),
             compare(py,comp,"OMC_SYSTEMDYNAMICS_VS_HINES_PYSD",a.tol)]
    # Independently verify the two OMC variants match at every stored point.
    surrogate=[]
    for row in eq:
        mapped={"time_hours":row.get("time",row.get("Time"))}
        for key,ref in FIELDS.items():mapped[ref]=get(row,key,True)
        surrogate.append(mapped)
    results.append(compare(surrogate,comp,"OMC_COMPONENTS_VS_OMC_EQUATIONS",a.tol))
    report={
        "experiment":"IGC_S1_HINES_PYSD_VS_OPENMODELICA_V1",
        "expected_time_grid":[0,8,0.25,33],
        "methods":{"pysd":"pysd 3.14.3 explicit Euler dt=0.25",
                   "openmodelica":"omc method=euler, numberOfIntervals=32, 0..8 hours"},
        "same_curve_coordinates":True,
        "same_synthetic_s1_inputs":True,
        "modelica_sources_are_original_restatement":True,
        "comparisons":results,
        "operationally_calibrated":False,
        "numerical_parity":all(item["all_points_within_tolerance"] for item in results),
        "library_components_compile_and_simulate":True,
        "library_composition_easy_or_superior":"NOT_MEASURED",
        "suitable_for_deciding_real_capacity":False,
        "source_files_not_redistributed":True,
        "inputs_sha256":{label:hashlib.sha256(path.read_bytes()).hexdigest() for label,path in
                          [("pysd",a.pysd),("omc_equations",a.equations),("omc_components",a.components)]}
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("S1_CROSS_ENGINE",json.dumps({"numerical_parity":report["numerical_parity"],
          "max_differences":{item["label"]:max(x["max_abs_error"] for x in item["fields"].values()) for item in results}}),flush=True)
    if not report["numerical_parity"]:raise SystemExit("OPENMODELICA_PYSD_PARITY_MISMATCH")

if __name__=="__main__":main()
