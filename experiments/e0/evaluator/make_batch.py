#!/usr/bin/env python3
"""Generate only independent evaluator test wrappers, NEVER a candidate constructor."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
REFERENCE = ("ZeroDirect","ZeroFilter","OneDirect","OneFilter","TwoDirect","TwoFilter")
PROBES = ("pulse","step","ramp","high_pulse")


def experiments(protocol):
    caps = protocol["parameter_policy"]["transit_capacity_per_h"]
    residence = protocol["parameter_policy"]["aggregate_residence_h"]
    if len(residence) != 1:
        raise ValueError("E0_REFERENCE_RESIDENCE_GRID_UNSUPPORTED")
    if tuple(x["id"] for x in protocol["interventions"]) != PROBES:
        raise ValueError("INTERVENTIONS_MUST_MATCH_PUBLIC_REFERENCE")
    for model in REFERENCE:
        for cap in caps:
            for i, probe in enumerate(PROBES,1):
                yield {
                    "model":model,"cap":cap,"probe":probe,"probe_number":i,
                    "name":model+"_cap"+str(cap)+"_"+probe,
                    "residence_h":residence[0]
                }


def build(output):
    protocol=json.loads((PARENT/"protocol.json").read_text(encoding="utf-8"))
    series=list(experiments(protocol))
    output.mkdir(parents=True,exist_ok=True)
    (output/"results").mkdir(exist_ok=True)
    models=["within;","package E0Batch"]
    commands=[
        'getVersion();',
        'loadModel(Modelica, {"4.0.0"});',
        'loadModel(SystemDynamics, {"2.1.2"});',
        'loadFile("../../../src/modelica/IGCMolecules.mo");',
        'loadFile("../../../src/modelica/IGCInformationMolecules.mo");',
        'loadFile("E0Reference.mo");',
        'loadFile("generated/E0Batch.mo");',
    ]
    for case in series:
        models.append("  model "+case["name"])
        models.append("    extends E0Reference."+case["model"]+
                      "(probe="+str(case["probe_number"])+
                      ",capacity="+str(case["cap"])+
                      ",residence="+str(case["residence_h"])+");")
        models.append("  end "+case["name"]+";")
        commands.append("checkModel(E0Batch."+case["name"]+");")
        commands.append(
            "simulate(E0Batch."+case["name"]+
            ',startTime=0,stopTime=8,numberOfIntervals=160,method="dassl"'+
            ',tolerance=1e-8,outputFormat="csv",fileNamePrefix="generated/results/'+
            case["name"]+'");')
    models.append("end E0Batch;")
    commands.append("getErrorString();")
    (output/"E0Batch.mo").write_text("\n".join(models)+"\n",encoding="utf-8")
    (output/"run.mos").write_text("\n".join(commands)+"\n",encoding="utf-8")
    (output/"cases.json").write_text(json.dumps(series,indent=2)+"\n",encoding="utf-8")
    print("E0_REFERENCE_BATCH",len(series),"controls; evaluator only; no oracle truth")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=HERE/"generated")
    args=p.parse_args()
    build(args.output)
