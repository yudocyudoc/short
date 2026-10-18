#!/usr/bin/env python3
"""Evaluator side of X1: numeric native outcomes, decision reversal, sealed truth.

There is no automatic PASS if all arms score well. This only checks whether the
worlds are informative *before* any participant makes decisions.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import secrets
from pathlib import Path
from build import CANDIDATES,ACTIONS,PROBES,UPGRADE_COST

HERE=Path(__file__).resolve().parent
COST={"none":0.0,"upgrade_preparation":UPGRADE_COST,"upgrade_distribution":UPGRADE_COST}
CASE_IDS=["C01","C02","C03","C04","C05","C06"]
NO_PROBE={"C06"}


def get(row,column):
    matches=[float(v) for k,v in row.items() if k==column or k.endswith("."+column)]
    if len(matches)!=1 or not math.isfinite(matches[0]):
        raise RuntimeError("BAD_NUMERIC_COLUMN:"+column)
    return matches[0]


def series(path):
    with Path(path).open(newline="",encoding="utf-8-sig") as fh:
        rows=list(csv.DictReader(fh))
    cleaned=[]
    for row in rows:
        t=get(row,"time")
        if cleaned and t<get(cleaned[-1],"time")-1e-8:
            raise RuntimeError("TIME_BACKWARDS")
        if cleaned and abs(get(cleaned[-1],"time")-t)<1e-8:
            cleaned[-1]=row
        else:cleaned.append(row)
    if len(cleaned)<100:
        raise RuntimeError("UNSIMULATED_MODEL:"+str(path))
    return cleaned


def at_time(rows,t,column):
    closest=min(rows,key=lambda row:abs(get(row,"time")-t))
    if abs(get(closest,"time")-t)>1e-5:
        raise RuntimeError("NUMERIC_GRID_MISSING_T"+str(t))
    return get(closest,column)


def candidates(folder):
    out={}
    for mechanism in CANDIDATES:
        out[mechanism]={"actions":{},"observables":{}}
        for action in ACTIONS:
            name="X_"+mechanism+"_"+action
            rows=series(folder/(name+"_res.csv"))
            deliveries=at_time(rows,8.0,"deliveredTotal")
            out[mechanism]["actions"][action]={
                 "delivery_by_8h":deliveries,
                 "upgrade_cost":COST[action],
                 "net_units":deliveries-COST[action]}
            if action=="none":
                for probe,profile in PROBES.items():
                    out[mechanism]["observables"][probe]=at_time(
                       rows,profile["hour"],profile["series"])
    return out


def preflight(numeric):
    options=candidates(numeric)
    best={m:max(ACTIONS,key=lambda a:options[m]["actions"][a]["net_units"]) for m in CANDIDATES}
    for m in CANDIDATES:
        values=sorted((v["net_units"] for v in options[m]["actions"].values()),reverse=True)
        if values[0]-values[1]<0.5:
            raise RuntimeError("NOT_DECISIONALLY_SEPARABLE:"+m)
        if best[m]=="none":
            raise RuntimeError("NO_MEANINGFUL_ACTION:"+m)
    if best[CANDIDATES[0]]==best[CANDIDATES[1]]:
        raise RuntimeError("SAME_OPTIMAL_DECISION_ACROSS_MECHANISMS")
    separating=[p for p in PROBES if abs(options[CANDIDATES[0]]["observables"][p]-
                                            options[CANDIDATES[1]]["observables"][p])>1e-4]
    if not separating:
        raise RuntimeError("NO_POSSIBLE_DISCRIMINATING_OBSERVATION")
    # The initial observation, request pattern, is identical in both models;
    # never expose a world-specific delivery trajectory before a probe.
    return options,{"status":"INFORMATIVE_WORLD_PRECHECK",
        "candidate_count":len(CANDIDATES),"optimal_actions_by_candidate":best,
        "separating_probes":separating,
        "no_probe_case_ids":sorted(NO_PROBE),
        "claim":"Preflight only; this is NOT a method result."}


def seal(options,out):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    secret_salt=os.urandom(32).hex()
    assignments={c:secrets.choice(CANDIDATES) for c in CASE_IDS}
    # Independent random assignments. If all mechanisms happen to be equal, the
    # report must be INCONCLUSIVE on cross-world diversity, never resample for PASS.
    truth={"world_by_case":assignments,"private_salt":secret_salt,
           "source":"native_OpenModelica_simulations","possible_models":CANDIDATES,
           "candidates":options,
           "issued_responses":{"initial":1,"probe_max":1,"reserved":1}}
    canonical=json.dumps({"world_by_case":assignments},sort_keys=True,separators=(",",":"))
    digest=hashlib.sha256((secret_salt+canonical).encode()).hexdigest()
    initial={
      "experiment":"IGC_X1_V4","phase":"initial","seal_sha256":digest,
      "cases":[{
          "id":case,
          "agent":"Responsable de una empresa pequeña que prepara y distribuye pedidos",
          "problem":"Una inversión sólo puede aumentar una de dos capacidades antes de la próxima jornada de demanda. ¿Cuál conviene?",
          "observation":"Se espera la misma secuencia conocida de picos de pedidos; no se dispone de inventarios internos ni del sitio del cuello de botella.",
          "actions":list(ACTIONS),
          "allowed_probes":[] if case in NO_PROBE else list(PROBES),
          "horizon_hours":8,
          "objective":"Maximizar entregas físicas por jornada menos costo de ampliación y de auditoría.",
          "probe_budget":0 if case in NO_PROBE else 1,
          "reserved_result":"resultado físico de la siguiente jornada idéntica, según acción"
      } for case in CASE_IDS],
      "probes":PROBES,
      "public_counterfactual_candidates":options,
      "limitations":["El universo candidato tiene sólo dos hipótesis conocidas; eso NO demuestra descubrimiento de mecanismos.",
                     "La nueva jornada reinicia stocks en cero; se supone repetibilidad exacta.",
                     "Se miden consecuencias decisionales, no generalización empresarial."]
    }
    (out/"private_truth.json").write_text(json.dumps(truth,indent=2)+"\n",encoding="utf-8")
    (out/"initial_public.json").write_text(json.dumps(initial,indent=2)+"\n",encoding="utf-8")
    print("X1_SEALED",json.dumps({"cases":len(CASE_IDS),
                                  "sha256":digest,
                                  "truth_assignments":"NOT_RELEASED"}))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--numeric",type=Path,required=True)
    p.add_argument("--public-out",type=Path,required=True)
    p.add_argument("--private-out",type=Path,required=True)
    a=p.parse_args()
    candidates_data,check=preflight(a.numeric)
    a.public_out.mkdir(parents=True,exist_ok=True)
    (a.public_out/"preflight.json").write_text(json.dumps(check,indent=2)+"\n")
    seal(candidates_data,a.private_out)
    # Only initial_public.json is copied to participant artifact.
    (a.public_out/"initial_public.json").write_text(
        (a.private_out/"initial_public.json").read_text(),encoding="utf-8")
    print("X1_EVALUATOR_PREFLIGHT",json.dumps(check))


if __name__=="__main__":
    main()
