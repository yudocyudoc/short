#!/usr/bin/env python3
"""Finite deterministic graph search over two INDEPENDENT optional mechanisms.

One optional physical transit BoundedQueue is inserted on FLOW<Shipment>.
One optional information FirstOrderReportFilter is attached to
SIGNAL<DeliveryRate>, never as a shipment queue.
The registered contracts determine wiring, not LLM text.
"""
from __future__ import annotations
import argparse,itertools,json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OPTIONAL=("TRANSIT","REPORT_FILTER")
ALIASES={(False,False):"Direct",(True,False):"TransitOnly",
         (False,True):"ReportOnly",(True,True):"TransitAndReport"}
PORTS={
 "SOURCE":{"out":("FLOW","Order")},
 "PREPARATION":{"in":("FLOW","Order"),"out":("FLOW","ReadyOrder")},
 "DISPATCH":{"in":("FLOW","ReadyOrder"),"out":("FLOW","Shipment")},
 "TRANSIT":{"in":("FLOW","Shipment"),"out":("FLOW","Shipment")},
 "DELIVERY":{"in":("FLOW","Shipment"),"reported":("SIGNAL","DeliveryRate")},
 "REPORT_FILTER":{"in":("SIGNAL","DeliveryRate"),"out":("SIGNAL","DeliveryRate")},
 "OBSERVED":{"in":("SIGNAL","DeliveryRate")}
}
NATIVE={
 "SOURCE.out":"accepted.outflow",
 "PREPARATION.in":"preparation.arrival",
 "PREPARATION.out":"preparation.completed",
 "DISPATCH.in":"dispatch.arrival",
 "DISPATCH.out":"dispatch.completed",
 "TRANSIT.in":"transit.arrival",
 "TRANSIT.out":"transit.completed",
 "DELIVERY.in":"delivered.arrival",
 "DELIVERY.reported":"reporter.physicalArrivalRate",
 "REPORT_FILTER.in":"reporter.physicalArrivalRate",
 "REPORT_FILTER.out":"reporter.reportedRate",
 "OBSERVED.in":"reportedDeliveryRate"
}
def verify_link(a,b):
    an,ap=a.split(".");bn,bp=b.split(".")
    aa=PORTS[an][ap];bb=PORTS[bn][bp]
    if aa!=bb:
        raise ValueError("INCOMPATIBLE_TYPED_EDGE:"+a+"->"+b)
def enumerate_graphs():
    catalog=json.loads((HERE/"catalog.json").read_text(encoding="utf-8"))
    registered={item["id"] for item in catalog["optional"]}
    if registered!=set(OPTIONAL):raise ValueError("UNKNOWN_OPTIONAL_MOLECULE")
    out=[]
    for use_transport,use_reporting in itertools.product((False,True),repeat=2):
        components=["SOURCE","PREPARATION","DISPATCH"]
        if use_transport:components.append("TRANSIT")
        components.append("DELIVERY")
        edges=[]
        for left,right in zip(components,components[1:]):
            a=left+".out";b=right+".in"
            verify_link(a,b)
            edges.append({"from":a,"to":b,"type":PORTS[left]["out"][0]+"<"+PORTS[left]["out"][1]+">"})
        if use_reporting:
            # The node named DELIVERY.reported is a conceptual physical receipt
            # rate SIGNAL, not a second output of the actual delivery stock.
            verify_link("DELIVERY.reported","REPORT_FILTER.in")
            edges.append({"from":"DELIVERY.reported","to":"REPORT_FILTER.in","type":"SIGNAL<DeliveryRate>"})
            verify_link("REPORT_FILTER.out","OBSERVED.in")
            edges.append({"from":"REPORT_FILTER.out","to":"OBSERVED.in","type":"SIGNAL<DeliveryRate>"})
            components.extend(["REPORT_FILTER","OBSERVED"])
        else:
            verify_link("DELIVERY.reported","OBSERVED.in")
            edges.append({"from":"DELIVERY.reported","to":"OBSERVED.in","type":"SIGNAL<DeliveryRate>"})
            components.append("OBSERVED")
        out.append({"id":ALIASES[(use_transport,use_reporting)],
            "components":components,"edges":edges,
            "optionals":[k for k,on in zip(OPTIONAL,(use_transport,use_reporting)) if on],
            "type_checked":True})
    return sorted(out,key=lambda x:x["id"])
def compile_graphs(graphs):
    if len(graphs)!=4 or {g["id"] for g in graphs}!=set(ALIASES.values()):
        raise ValueError("MISSING_OPTIONAL_VARIANT")
    lines=["within;","package IGCObservationGraphs"]
    for graph in graphs:
        use_t="TRANSIT" in graph["optionals"]
        use_r="REPORT_FILTER" in graph["optionals"]
        if graph["id"]!=ALIASES[(use_t,use_r)] or set(graph["optionals"])-set(OPTIONAL):
            raise ValueError("GRAPH_OPTION_SET_MISMATCH")
        lines.extend(["  model "+graph["id"],"    extends IGCObservationCore.Upstream;"])
        if use_t:
            lines.extend(["    IGCMolecules.BoundedQueue transit(",
                          "      maxThroughput=transitCapacity,",
                          "      responseTime=transitResponseTime);"])
        if use_r:
            lines.append("    IGCInformationMolecules.FirstOrderReportFilter reporter;")
        lines.append("  equation")
        for edge in graph["edges"]:
            source,dest=edge["from"],edge["to"]
            if source in ("SOURCE.out","PREPARATION.out"):continue
            if source in ("DELIVERY.reported","REPORT_FILTER.out"):
                # This is a signal observation of a native REAL variable,
                # not a material-flow connect() operation.
                continue
            if source=="DISPATCH.out" and dest=="DELIVERY.in":
                lines.append("    connect(dispatch.completed,delivered.arrival);")
            elif source=="DISPATCH.out" and dest=="TRANSIT.in":
                lines.append("    connect(dispatch.completed,transit.arrival);")
            elif source=="TRANSIT.out" and dest=="DELIVERY.in":
                lines.append("    connect(transit.completed,delivered.arrival);")
            else:raise ValueError("NO_APPROVED_NATIVE_CONNECTOR:"+source+":"+dest)
        if use_t:
            lines.extend(["    deliveryRate = transit.completed;",
                          "    inTransit = transit.waiting;"])
        else:
            lines.extend(["    deliveryRate = dispatch.completed;",
                          "    inTransit = 0;"])
        if use_r:
            lines.extend(["    reporter.physicalArrivalRate = deliveryRate;",
                          "    reportedDeliveryRate = reporter.reportedRate;"])
        else:
            lines.append("    reportedDeliveryRate = deliveryRate;")
        lines.append("  end "+graph["id"]+";")
    lines.extend(['  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));',
                  "end IGCObservationGraphs;",""])
    text="\n".join(lines)
    if "der(" in text:raise ValueError("MATH_OUTSIDE_TRUSTED_MOLECULES")
    return text
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--model",type=Path,required=True)
    a.add_argument("--manifest",type=Path,required=True)
    x=a.parse_args()
    graphs=enumerate_graphs()
    x.model.parent.mkdir(parents=True,exist_ok=True)
    x.manifest.parent.mkdir(parents=True,exist_ok=True)
    x.model.write_text(compile_graphs(graphs),encoding="utf-8")
    x.manifest.write_text(json.dumps({"graphs":graphs,"n":len(graphs),
          "llm_generated_equations":0,
          "scope":"2 independent typed optionals; native S2 upstream remains fixed",
          "physical_vs_information_separated":True},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("IGC_ENUMERATED",json.dumps([g["id"] for g in graphs]),flush=True)
if __name__=="__main__":main()
