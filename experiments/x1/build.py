#!/usr/bin/env python3
"""X1 -- construct two rival bottleneck worlds via E1 only; no LLM AST.

Generates public counterfactual scenarios for an *idealized repeatable workday*.
No secret assignment of cases to worlds is stored in this file.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/"experiments"/"e1"))
import composer
import backend

REGISTRY=ROOT/"experiments"/"e1"/"registry.base.json"
CAP_HIGH=20
CAP_LOW=3
CAP_UPGRADE=12
UPGRADE_COST=2.0
REQUEST_STIMULUS=4  # E1 high pulse: 14/h, starting 1h, width 40%, period 4h
CANDIDATES=("M_A","M_B")
ACTIONS=("none","upgrade_preparation","upgrade_distribution")
PROBES={
 "measure_departures":{"series":"dispatchRate","hour":4.0,"cost":0.8,
                        "explanation":"Recontar unidades por hora que salen del centro"},
 "measure_in_route":{"series":"inTransit","hour":4.0,"cost":1.1,
                        "explanation":"Contar unidades expedidas todavía no recibidas"},
 "inspect_dashboard":{"series":"reportedDeliveryRate","hour":4.0,"cost":0.2,
                        "explanation":"Leer el indicador existente sin auditoría física"},
}
# Models are parameterized *mechanisms*, not graph names read from text.
# Both use the same valid topology but have bottlenecks at different stages.
VARIANTS={
 "M_A":{"preparation":CAP_LOW,"transit":CAP_HIGH},
 "M_B":{"preparation":CAP_HIGH,"transit":CAP_LOW},
}


def base_graph():
    cfg,classes,_=composer.load_registry(REGISTRY)
    possible=composer.enumerate_graphs(cfg,classes)
    # Select by graph *properties* (not case identity, not hidden truth).
    matches=[copy.deepcopy(g) for _,g in possible if
             sum(i["role"]=="transit" for i in g["instances"])==1 and
             not any(i["role"]=="report" for i in g["instances"])]
    if len(matches)!=1:
        raise RuntimeError("E1_NO_UNIQUE_ONE_TRANSIT_BASE")
    return cfg,classes,matches[0]


def updated(graph,model,action):
    g=copy.deepcopy(graph)
    for inst in g["instances"]:
        role=inst["role"]
        if role not in ("preparation","transit"): continue
        bottleneck=VARIANTS[model][role]
        if (role=="preparation" and action=="upgrade_preparation") or (
            role=="transit" and action=="upgrade_distribution"):
            bottleneck=max(bottleneck,CAP_UPGRADE)
        inst["parameters"]["maxThroughput"]=bottleneck
        if role=="transit":inst["parameters"]["responseTime"]=1.6
    return g


def generate(dest):
    dest=Path(dest)
    dest.mkdir(parents=True,exist_ok=True)
    (dest/"results").mkdir(exist_ok=True)
    cfg,cl,g=base_graph()
    models=[]
    registry=[]
    for m in CANDIDATES:
        for a in ACTIONS:
            name="X_"+m+"_"+a
            current=updated(g,m,a)
            native=backend.render_model(name,current,cfg,cl).replace("parameter Integer probe(min=1,max=4)=1;","parameter Integer probe(min=1,max=4)=4;")
            if "der(" in native:
                raise RuntimeError("NEW_DIFFERENTIAL_EQUATION_FORBIDDEN")
            composer.check_graph(current,cfg,cl)
            models.append(native)
            registry.append({"candidate":m,"action":a,"model_name":name,
                             "ast_hash":composer.canonical(current)})
    modelica="within;\npackage X1Alternatives\n"+"\n".join(models)+"\nend X1Alternatives;\n"
    (dest/"X1Alternatives.mo").write_text(modelica,encoding="utf-8")
    script=[
      'getVersion();',
      'loadModel(Modelica, {"4.0.0"});',
      'loadModel(SystemDynamics, {"2.1.2"});',
      'loadFile("../../src/modelica/IGCMolecules.mo");',
      'loadFile("../../src/modelica/IGCInformationMolecules.mo");',
      'loadFile("generated/X1Alternatives.mo");'
    ]
    for rec in registry:
        name=rec["model_name"]
        script.append("checkModel(X1Alternatives."+name+");")
        script.append('simulate(X1Alternatives.'+name+
            ',startTime=0,stopTime=8,numberOfIntervals=160,method="dassl",'+
            'tolerance=1e-8,outputFormat="csv",fileNamePrefix="generated/results/'+name+'",'+
            'simflags="-override probe=4");')
    script.append('getErrorString();')
    (dest/"run.mos").write_text("\n".join(script)+"\n",encoding="utf-8")
    (dest/"registry_generated.json").write_text(json.dumps(registry,indent=2)+"\n")
    print("X1_GENERATED",len(registry),"models; E1 compiler reused, no LLM modelling")


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,default=HERE/"generated")
    generate(p.parse_args().out)
