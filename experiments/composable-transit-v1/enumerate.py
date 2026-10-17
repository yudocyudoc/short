#!/usr/bin/env python3
"""Enumerate genuinely connected optional molecular graphs, then trusted Modelica.

The stage catalog has exactly one optional molecule TRANSIT. The generator
derives edges from typed ports, not hard-coded S2 REQUIRED_LINKS. The
composition renderer introduces native new connect() statements, not
selection between two existing full macros.
"""
from __future__ import annotations
import argparse,itertools,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def data():return json.loads((HERE/"catalog.json").read_text(encoding="utf-8"))

def enumerate_graphs():
    cat=data();stages=cat["stages"]
    must=[s for s in stages if s["mandatory"]]
    maybe=[s for s in stages if not s["mandatory"]]
    out=[]
    for flags in itertools.product((False,True),repeat=len(maybe)):
        selected={s["id"] for s in must}|{s["id"] for s,f in zip(maybe,flags) if f}
        chain=["SOURCE"]+[s["id"] for s in stages if s["id"] in selected]+["DELIVERY"]
        contracts={"SOURCE":cat["boundary"]["SOURCE"],
                   "DELIVERY":cat["boundary"]["DELIVERY"]}
        contracts.update({s["id"]:s for s in stages})
        links=[];good=True
        for left,right in zip(chain,chain[1:]):
            a=contracts[left].get("out",contracts[left].get("ports",{}).get("out"))
            b=contracts[right].get("in",contracts[right].get("ports",{}).get("in"))
            if a is None or a!=b:good=False;break
            links.append({"from":left+".out","to":right+".in","type":a})
        if not good:continue
        title="Buffered" if "TRANSIT" in chain else "Direct"
        out.append({"id":title,"nodes":chain,"links":links,
            "optional_molecules":[s for s in selected if s in {m["id"] for m in maybe}],
            "type_checked":True})
    return sorted(out,key=lambda x:x["id"])

def checked(candidates):
    titles={x["id"] for x in candidates}
    if titles!={"Direct","Buffered"}:raise ValueError("NO_TWO_DISTINCT_TYPED_GRAPHS")
    for x in candidates:
        if x["nodes"][0]!="SOURCE" or x["nodes"][-1]!="DELIVERY":
            raise ValueError("BAD_TERMINAL")
        if len(x["links"])!=len(x["nodes"])-1:
            raise ValueError("DISCONNECTED_GRAPH")
    return True

# Native names and connector field names are preaudited, not read from the LLM
BACKEND_PORTS={"SOURCE":{"out":"accepted.outflow"},
  "PREPARATION":{"in":"preparation.arrival","out":"preparation.completed"},
  "DISPATCH":{"in":"dispatch.arrival","out":"dispatch.completed"},
  "TRANSIT":{"in":"transit.arrival","out":"transit.completed"},
  "DELIVERY":{"in":"delivered.arrival"}}

def emit_model(graph):
    allowed={"SOURCE","PREPARATION","DISPATCH","TRANSIT","DELIVERY"}
    if set(graph["nodes"])-allowed:raise ValueError("UNREGISTERED_COMPONENT")
    if len(set(graph["nodes"]))!=len(graph["nodes"]):raise ValueError("DUPLICATE_COMPONENT")
    if graph["id"] not in {"Direct","Buffered"}:raise ValueError("UNAPPROVED_GRAPH_ID")
    if graph["id"]=="Direct" and "TRANSIT" in graph["nodes"]:
        raise ValueError("CONTRADICTORY_GRAPH_ID")
    if graph["id"]=="Buffered" and "TRANSIT" not in graph["nodes"]:
        raise ValueError("CONTRADICTORY_GRAPH_ID")
    result=["  model "+graph["id"],
      "    extends IGCTransitCore.Upstream;"]
    # Connections inside the fixed upstream molecule are already declared.
    if "TRANSIT" in graph["nodes"]:
        result.extend(["    IGCMolecules.BoundedQueue transit(",
          "      maxThroughput=transitCapacity,",
          "      responseTime=transitResponseTime);"])
    result.append("  equation")
    for link in graph["links"]:
        a,ap=link["from"].split(".");b,bp=link["to"].split(".")
        if (a,b) in {("SOURCE","PREPARATION"),("PREPARATION","DISPATCH")}:
            continue
        sa=BACKEND_PORTS[a][ap];sb=BACKEND_PORTS[b][bp]
        result.append("    connect("+sa+","+sb+");")
    if "TRANSIT" in graph["nodes"]:
        result.extend(["    deliveryRate = transit.completed;",
                       "    inTransit = transit.waiting;"])
    else:
        result.extend(["    deliveryRate = dispatch.completed;",
                       "    inTransit = 0;"])
    result.append("  end "+graph["id"]+";")
    return result

def render(graphs):
    checked(graphs)
    lines=["within;","package IGCTransitGraphs"]
    for g in graphs:lines.extend(emit_model(g))
    lines+=['  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));',
             "end IGCTransitGraphs;",""]
    src="\n".join(lines)
    if "der(" in src:raise ValueError("UNTRUSTED_EQUATION")
    return src

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--graph-report",type=Path,required=True)
    args=p.parse_args()
    graphs=enumerate_graphs()
    source=render(graphs)
    args.source.parent.mkdir(parents=True,exist_ok=True)
    args.source.write_text(source,encoding="utf-8")
    args.graph_report.write_text(json.dumps({"variants":graphs,
      "count":len(graphs),
      "equations_from_llm":0,
      "composition_method":"enumeration of typed optional molecule + deterministic Modelica wiring"},
      ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("COMPOSABLE_TYPED_GRAPHS",json.dumps([g["id"] for g in graphs]),flush=True)
if __name__=="__main__":main()
