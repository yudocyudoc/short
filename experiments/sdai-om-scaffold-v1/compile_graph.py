#!/usr/bin/env python3
"""IGC bounded SD graph -> existing OpenModelica components, never LLM equations.

The only generated Modelica text is assembled from trusted, fixed port/wiring
templates. The LLM is prohibited from supplying arbitrary equations, code,
component names or numeric parameters. The generated model reuses validated
SystemDynamics rates/levels plus Modelica.Blocks.Math.Gain response policies.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REQUIRED_ROLES=(
 "incoming_orders","unprepared_work","preparation",
 "prepared_work","dispatch","delivered")
MAT_LINKS=(
 ("incoming_orders","unprepared_work"),
 ("unprepared_work","preparation"),
 ("preparation","prepared_work"),
 ("prepared_work","dispatch"),
 ("dispatch","delivered"))
CONTROL_LINKS=(
 ("unprepared_work","preparation","+"),
 ("prepared_work","dispatch","+"))
# Mapping from semantic directed material links to TESTED native ports.
PORT_WIRING={
 ("incoming_orders","unprepared_work"):
     "connect(incoming_orders.y,unprepared_work.u1);",
 ("unprepared_work","preparation"):
     "connect(preparation.y1,unprepared_work.u2);",
 ("preparation","prepared_work"):
     "connect(preparation.y,prepared_work.u1);",
 ("prepared_work","dispatch"):
     "connect(dispatch.y1,prepared_work.u2);",
 ("dispatch","delivered"):
     "connect(dispatch.y,delivered.u1);"}
SOURCES={
 "incoming_orders":{"F1"},"unprepared_work":{"F1","F2"},
 "preparation":{"F2"},"prepared_work":{"F2","F3"},
 "dispatch":{"F3"},"delivered":{"F3"}}
MATERIAL_EVIDENCE={
 ("incoming_orders","unprepared_work"):{"F1"},
 ("unprepared_work","preparation"):{"F2"},
 ("preparation","prepared_work"):{"F2"},
 ("prepared_work","dispatch"):{"F3"},
 ("dispatch","delivered"):{"F3"}}
CONTROL_EVIDENCE={
 ("unprepared_work","preparation","+"):{"F2"},
 ("prepared_work","dispatch","+"):{"F3"}}

def read(name):
    return json.loads((HERE/name).read_text(encoding="utf-8"))

def invalid(reason,case_id):
    return {"status":"REJECTED","reason":reason,"case_id":case_id,
            "modelica_generated":False,"simulation_authorized":False}

def valid_ref(refs,allow):
    return isinstance(refs,list) and bool(refs) and all(
        isinstance(v,str) and v in allow for v in refs)

def verify(case_id,proposal):
    cases={x["id"]:x for x in read("cases_public.json")["cases"]}
    catalog=read("catalog.json")
    if case_id not in cases:raise ValueError("UNKNOWN_CASE")
    case=cases[case_id]
    if not isinstance(proposal,dict):
        return invalid("RESPONSE_NOT_JSON_OBJECT",case_id)
    if set(proposal)!={"nodes","material_links","causal_links","decision","numeric_evidence","missing","feedback_loops"}:
        return invalid("INVALID_RESPONSE_SCHEMA",case_id)
    action=proposal["decision"]
    if action not in ("SIMULATE_SYNTHETIC","STRUCTURE_ONLY","ABSTAIN"):
        return invalid("INVALID_ACTION",case_id)
    if not isinstance(proposal["missing"],list) or not all(
        isinstance(s,str) and 0<len(s)<=200 for s in proposal["missing"]):
        return invalid("INVALID_MISSING_INFORMATION",case_id)
    if not isinstance(proposal["feedback_loops"],list):
        return invalid("INVALID_FEEDBACK_LOOPS",case_id)
    supported_loops={
        ("unprepared_work","preparation","unprepared_work"):{"F2"},
        ("prepared_work","dispatch","prepared_work"):{"F3"}}
    seen_loops=set()
    for loop in proposal["feedback_loops"]:
        if not isinstance(loop,dict) or set(loop)!={"path","kind","evidence"}:
            return invalid("INVALID_FEEDBACK_LOOP_SCHEMA",case_id)
        sequence=loop["path"]
        if not isinstance(sequence,list) or len(sequence)!=3:
            return invalid("UNSUPPORTED_FEEDBACK_LOOP",case_id)
        try: key=tuple(sequence)
        except TypeError:return invalid("INVALID_FEEDBACK_LOOP_PATH",case_id)
        if key not in supported_loops or key in seen_loops or loop["kind"]!="B":
            return invalid("UNSUPPORTED_OR_DUPLICATE_FEEDBACK_LOOP",case_id)
        seen_loops.add(key)
        if not valid_ref(loop["evidence"],{f["id"] for f in case["facts"]}) or not (
            supported_loops[key].intersection(loop["evidence"])):
            return invalid("UNGROUNDED_FEEDBACK_LOOP",case_id)
    facts={item["id"] for item in case["facts"]}
    if not isinstance(proposal["numeric_evidence"],list) or any(
        x not in facts for x in proposal["numeric_evidence"]):
        return invalid("INVALID_NUMERIC_EVIDENCE",case_id)
    if case["kind"]=="INDETERMINATE":
        if action!="ABSTAIN" or proposal["nodes"] or proposal["material_links"] or proposal["causal_links"] or proposal["numeric_evidence"] or not proposal["missing"]:
            return invalid("UNRESOLVED_PROBLEM_MUST_ABSTAIN",case_id)
        return {"status":"VALID_ABSTENTION","case_id":case_id,
                "modelica_generated":False,"simulation_authorized":False,
                "missing":proposal["missing"]}
    if not isinstance(proposal["nodes"],list) or len(proposal["nodes"])!=6:
        return invalid("STOCK_FLOW_GRAPH_INCOMPLETE",case_id)
    observed={}
    for node in proposal["nodes"]:
        if not isinstance(node,dict) or set(node)!={"role","kind","label","evidence"}:
            return invalid("INVALID_NODE_SCHEMA",case_id)
        role=node["role"]
        if not isinstance(role,str) or role in observed or role not in catalog["roles"]:
            return invalid("UNSUPPORTED_OR_DUPLICATE_ROLE",case_id)
        if node["kind"]!=catalog["roles"][role]["kind"]:
            return invalid("STOCK_FLOW_TYPE_MISMATCH",case_id)
        if not isinstance(node["label"],str) or not 1<=len(node["label"])<=100:
            return invalid("INVALID_NODE_LABEL",case_id)
        if not valid_ref(node["evidence"],facts) or not (
                SOURCES[role].intersection(node["evidence"])):
            return invalid("UNGROUNDED_NODE",case_id)
        observed[role]=node
    if set(observed)!=set(REQUIRED_ROLES):
        return invalid("UNSUPPORTED_TOPOLOGY",case_id)

    if not isinstance(proposal["material_links"],list) or len(proposal["material_links"])!=5:
        return invalid("INCOMPLETE_MATERIAL_FLOW",case_id)
    actual=[]
    for link in proposal["material_links"]:
        if not isinstance(link,dict) or set(link)!={"source","target","evidence"}:
            return invalid("INVALID_FLOW_LINK_SCHEMA",case_id)
        pair=(link["source"],link["target"])
        if pair not in MATERIAL_EVIDENCE or not valid_ref(link["evidence"],facts) or not (
            MATERIAL_EVIDENCE[pair].intersection(link["evidence"])):
            return invalid("UNSUPPORTED_OR_UNGROUNDED_MATERIAL_LINK",case_id)
        actual.append(pair)
    if len(set(actual))!=5 or set(actual)!=set(MAT_LINKS):
        return invalid("BAD_FLOW_GRAPH",case_id)

    if not isinstance(proposal["causal_links"],list) or len(proposal["causal_links"])!=2:
        return invalid("MISSING_CAUSAL_RESPONSE_LINKS",case_id)
    signals=[]
    for link in proposal["causal_links"]:
        if not isinstance(link,dict) or set(link)!={"source","target","polarity","evidence"}:
            return invalid("INVALID_CAUSAL_LINK_SCHEMA",case_id)
        k=(link["source"],link["target"],link["polarity"])
        if k not in CONTROL_EVIDENCE or not valid_ref(link["evidence"],facts) or not (
            CONTROL_EVIDENCE[k].intersection(link["evidence"])):
            return invalid("UNSUPPORTED_CAUSAL_POLARITY_OR_CITATION",case_id)
        signals.append(k)
    if len(set(signals))!=2 or set(signals)!=set(CONTROL_LINKS):
        return invalid("CAUSAL_GRAPH_MISMATCH",case_id)
    if action=="ABSTAIN":
        return {"status":"VALID_CONSERVATIVE_ABSTENTION","case_id":case_id,
                "modelica_generated":False,"simulation_authorized":False}
    if action=="SIMULATE_SYNTHETIC" and not (case["kind"]=="SYNTHETIC_COMPLETE" and
                                            "F4" in proposal["numeric_evidence"]):
        return invalid("NO_VERIFIED_COMPLETE_SYNTHETIC_INPUTS",case_id)
    if action=="STRUCTURE_ONLY" and not proposal["missing"]:
        return invalid("STRUCTURE_ONLY_NEEDS_OPEN_QUESTIONS",case_id)
    if case["kind"]=="STRUCTURE_ONLY" and action!="STRUCTURE_ONLY":
        return invalid("INSUFFICIENT_NUMERIC_EVIDENCE",case_id)
    return {"status":("READY_FOR_SYNTHETIC_OMC" if action=="SIMULATE_SYNTHETIC"
                      else "STRUCTURE_ONLY"),"case_id":case_id,
            "modelica_generated":action=="SIMULATE_SYNTHETIC",
            "simulation_authorized":action=="SIMULATE_SYNTHETIC",
            "reused_classes":sorted({catalog["roles"][r]["class"] for r in observed}),
            "reused_policy_classes":["Modelica.Blocks.Math.Gain",
                                      "SystemDynamics.Rates.RRate"],
            "stocks":3,"flows":3,"material_links":5,"causal_links":2,
            "free_form_equations_accepted":0,
            "model_source":"trusted_catalog_and_port_templates",
            "missing":proposal["missing"]}

def render(proposal):
    # Only call following verify == READY_FOR_SYNTHETIC_OMC.
    # Static set of known port connections; graph determines inclusion/order.
    cat=read("catalog.json")["roles"]
    roles={n["role"] for n in proposal["nodes"]}
    decl={
     "incoming_orders":"SystemDynamics.Rates.Rate_1 incoming_orders;",
     "unprepared_work":"SystemDynamics.Levels.Level unprepared_work(x0=0);",
     "preparation":"SystemDynamics.Rates.RRate preparation(minFlow=0,maxFlow=capacityPreparing);",
     "prepared_work":"SystemDynamics.Levels.Level prepared_work(x0=0);",
     "dispatch":"SystemDynamics.Rates.RRate dispatch(minFlow=0,maxFlow=capacityDispatch);",
     "delivered":"SystemDynamics.Levels.Level1a delivered(x0=0);"}
    if roles!=set(decl):raise ValueError("UNSUPPORTED_TOPOLOGY")
    lines=["within;","package IGCAutoAssembled",
           "  model Components","    extends IGCS2MakeToOrder.Scenario;"]
    lines.extend("    "+decl[role] for role in REQUIRED_ROLES)
    lines.extend([
      "    Modelica.Blocks.Math.Gain preparation_response(k=1/preparationResponseTime);",
      "    Modelica.Blocks.Math.Gain dispatch_response(k=1/dispatchResponseTime);",
      "  equation",
      "    incoming_orders.u = acceptedRate;",
      "    preparation_response.u = unprepared_work.level;",
      "    dispatch_response.u = prepared_work.level;",
      "    connect(preparation_response.y,preparation.u);",
      "    connect(dispatch_response.y,dispatch.u);"])
    # Edges arise from validated proposal; formulas and Modelica strings DO NOT.
    for link in proposal["material_links"]:
        lines.append("    "+PORT_WIRING[(link["source"],link["target"])])
    lines.extend([
     "    unpreparedOrders = unprepared_work.level;",
     "    preparedOrders = prepared_work.level;",
     "    deliveredOrders = delivered.level;",
     "    preparationRate = preparation.rate;",
     "    dispatchRate = dispatch.rate;",
     "  end Components;",
     '  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));',
     "end IGCAutoAssembled;",""])
    source="\n".join(lines)
    if "der(" in source:raise ValueError("MODEL_MUST_USE_LIBRARY_STOCKS")
    for forbidden in ('exec(', 'import ', 'system('):
        if forbidden in source:raise ValueError("BAD_GENERATED_CODE")
    return source

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--case",required=True,choices=("G01","G02","G03","G04"))
    p.add_argument("--proposal",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--model",type=Path)
    a=p.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    try: response=json.loads(a.proposal.read_text(encoding="utf-8"))
    except (ValueError,UnicodeError) as exc:result=invalid("BAD_JSON",a.case)
    else:result=verify(a.case,response)
    if a.model and result["status"]=="READY_FOR_SYNTHETIC_OMC":
        a.model.parent.mkdir(parents=True,exist_ok=True)
        a.model.write_text(render(response),encoding="utf-8")
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("IGC_SD_AI_COMPONENT_GATE",json.dumps({"status":result["status"],
         "case":a.case,"simulation_authorized":result["simulation_authorized"]}),
         flush=True)
    if result["status"]=="REJECTED":raise SystemExit(2)

if __name__=="__main__":main()
