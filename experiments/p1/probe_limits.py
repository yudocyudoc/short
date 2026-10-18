#!/usr/bin/env python3
"""P1 negative-capability probes against unchanged E1.

This does NOT implement a new linter, parser, policy or Modelica molecule.
Synthetic ports are in-memory probes of the old linter only, NEVER executable
classes. Every observed E1 error is retained, including over-rejections.
"""
import copy
import json
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/"experiments/e1"))
import composer

def port(name,direction,typ,unit="people/hour",entity=None):
    p={"name":name,"direction":direction,"type":typ,"unit":unit}
    if entity is not None:p["entity_domain"]=entity
    return p

def cls(id,role,ports,mechanism):
    return {"id":id,"roles":[role],"ports":ports,"parameters":{},
            "modelica":"NO_REAL_MODEL_"+id.replace("-","_"),
            "mechanism":mechanism}

def synthetic_registry():
    # Abstract P1 contract, intentionally NOT added to any executable registry.
    classes={
       "p1-source":cls("p1-source","source",[
           port("outflow","out","FLOW<Customer>")],"A customer-only boundary source"),
       "p1-queue":cls("p1-queue","queue",[
           port("arrival","in","FLOW<Customer>"),
           port("served","out","FLOW<Customer>"),
           port("left","out","FLOW<Customer>"),
           port("waiting","out","STATE<Customer>","people")],
           "Waiting stock, two independent controlled outflows with conservation requirement"),
       "p1-served":cls("p1-served","receipt",[
           port("arrival","in","FLOW<Customer>")],"Boundary receiving served customers"),
       "p1-left":cls("p1-left","abandoned",[
           port("arrival","in","FLOW<Customer>")],"Boundary receiving customers leaving"),
    }
    cfg={"mandatory_roles":["source","receipt"],"roles":{
        r:{"class_id":name,"max_instances":1,"parameters":{}}
        for r,name in [("source","p1-source"),("queue","p1-queue"),
                       ("receipt","p1-served"),("abandoned","p1-left")]},
         "endpoints":{"source":{"role":"source","output":"outflow"},
                      "receipt":{"role":"receipt","input":"arrival"},
                      "receipt_rate_tap":{"id":"receipt-rate-tap","observable":"SIGNAL<DeliveryRate>"}}}
    nodes=[{"id":id,"role":role,"class_id":cl,"parameters":{}} for id,role,cl in
           [("source0","source","p1-source"),("queue0","queue","p1-queue"),
            ("receipt0","receipt","p1-served"),("abandoned0","abandoned","p1-left")]]
    return cfg,classes,nodes

def edge(a,b):return {"from":a,"to":b,"adapter":None}
def old_linter_error(graph,cfg,classes):
    try:composer.check_graph(graph,cfg,classes)
    except (ValueError,KeyError,TypeError,StopIteration) as x:return type(x).__name__+":"+str(x)
    return "ACCEPTED"

def reference_conservation(topology):
    # A MINIMAL formal reference for the *fixture*, not a new runtime linter.
    # Only enumerated material origins are checked; two separate outflow names
    # from a declared stock are qualitatively admissible, not numerically tested.
    links=topology["links"]
    outgoing={}
    for e in links:outgoing.setdefault(e["from"],[]).append(e["to"])
    return not any(len(targets)>1 for targets in outgoing.values())

def p1_cases():
    cfg,cl,nodes=synthetic_registry()
    pos={"instances":copy.deepcopy(nodes),"links":[
       edge("source0.outflow","queue0.arrival"),
       edge("queue0.served","receipt0.arrival"),
       edge("queue0.left","abandoned0.arrival")
    ]}
    neg={"instances":copy.deepcopy(nodes),"links":[
       edge("source0.outflow","queue0.arrival"),
       edge("queue0.served","receipt0.arrival"),
       edge("queue0.served","abandoned0.arrival")
    ]}
    pos_old=old_linter_error(pos,cfg,cl)
    neg_old=old_linter_error(neg,cfg,cl)
    if not reference_conservation(pos) or reference_conservation(neg):
        raise RuntimeError("P1_REFERENCE_FIXTURE_BAD")
    if "MATERIAL_MULTICAST" not in pos_old or "MATERIAL_MULTICAST" not in neg_old:
        raise RuntimeError("P1_E1_LIMIT_NOT_REPRODUCED:"+pos_old+"/"+neg_old)
    result=[
     {"case":"POS-01","question":"two independent outputs of one stock, conservation unresolved numerically",
      "fixture_reference":"STRUCTURALLY_POSSIBLE_NOT_EXECUTABLE_WITHOUT_POLICY",
      "observed_e1":pos_old,
      "finding":"OVER_REJECTION: one-successor rule rejects legitimate stock split"},
     {"case":"NEG-01","question":"same physical output duplicated to two receivers",
      "fixture_reference":"REJECT_MATERIAL_DUPLICATION",
      "observed_e1":neg_old,
      "finding":"REJECTION_OCCURS but conflates cloning with valid branching"},
    ]
    # Compare an E1-valid topology with a semantically altered purpose. The
    # linter checks registered signatures but NOT whether semantic purpose
    # agrees with case evidence.
    base_cfg,base_cl,_=composer.load_registry(ROOT/"experiments/e1/registry.base.json")
    graphs=composer.enumerate_graphs(base_cfg,base_cl)
    example=copy.deepcopy(graphs[0][1])
    if old_linter_error(example,base_cfg,base_cl)!="ACCEPTED":
        raise RuntimeError("E1_BASELINE_NOT_ACCEPTED")
    adversarial=copy.deepcopy(base_cl)
    adversarial["bounded-queue"]["mechanism"]="Infection spreading between interacting individuals; no cafe evidence"
    response=old_linter_error(example,base_cfg,adversarial)
    if response!="ACCEPTED":raise RuntimeError("P1_SEMANTIC_INVARIANCE_CHANGED")
    result.append({"case":"NEG-02","question":"identical valid typed graph but unrelated causal purpose",
      "fixture_reference":"EVIDENCE_REQUIRED_NOT_EXECUTABLE_AS_EXPLANATION",
      "observed_e1":response,
      "finding":"SEMANTIC_PURPOSE_NOT_VALIDATED (test alters mock catalog metadata only)"})
    # The original E1 registered classes expose no CONTROL input nor general
    # policy interface. Nonexistence != correctly classified abstention.
    controls=[(ident,p["name"]) for ident,c in base_cl.items()
              for p in c["ports"] if p["type"].startswith("CONTROL<")]
    if controls:raise RuntimeError("P1_CONTROL_ALREADY_EXISTS")
    result.append({"case":"NEG-03","question":"waiting-dependent capacity/abandonment without registered law or CONTROL",
      "fixture_reference":"POLICY_UNIMPLEMENTED_OR_NO_MATCHING_MOLECULE",
      "observed_e1":"NO_CONTROL_PORT_OR_POLICY: no structured abstention status",
      "finding":"UNREPRESENTABLE_AND_NO_SEMANTIC_DIAGNOSTIC"})
    # Reusability by semantics remains a CONDITIONAL candidate, not a
    # claim that the currently role-bound BoundedQueue can take customers.
    roles=base_cl["bounded-queue"]["roles"]
    result.append({"case":"POS-02","question":"generic bounded storage reused for a Customer stock",
      "fixture_reference":"CONDITIONALLY_REUSABLE_AFTER_VERIFIED_ENTITY_BINDING",
      "observed_e1":"ROLE_NOT_SUPPORTED:customer" if "customer" not in roles else "ROLE_EXISTS",
      "finding":"CUSTOMER_ROLE_AND_NATIVE_BINDING_NOT_ADMITTED_YET"})
    # Additional independent negative probe: same dimensional units can hide
    # distinct entities and still look equal to a simplistic port checker.
    cfg2={"mandatory_roles":["source","receipt"],"roles":{
      "source":{"class_id":"entity-source","max_instances":1,"parameters":{}},
      "receipt":{"class_id":"entity-receipt","max_instances":1,"parameters":{}}},
      "endpoints":{"source":{"role":"source","output":"outflow"},
        "receipt":{"role":"receipt","input":"arrival"},
        "receipt_rate_tap":{"id":"receipt-rate-tap","observable":"SIGNAL<DeliveryRate>"}}}
    cl2={"entity-source":cls("entity-source","source",
          [port("outflow","out","FLOW<Person>",entity="CUSTOMER")],"Customers"),
         "entity-receipt":cls("entity-receipt","receipt",
          [port("arrival","in","FLOW<Person>",entity="EMPLOYEE")],"Employees")}
    g2={"instances":[{"id":"source0","role":"source","class_id":"entity-source","parameters":{}},
                     {"id":"receipt0","role":"receipt","class_id":"entity-receipt","parameters":{}}],
        "links":[edge("source0.outflow","receipt0.arrival")]}
    res=old_linter_error(g2,cfg2,cl2)
    if res!="ACCEPTED":raise RuntimeError("P1_DOMAIN_MISMATCH_NOT_REPRODUCED:"+res)
    result.append({"case":"NEG-04_SUPPLEMENTAL","question":"FLOW<Person> customer and employee endpoint with same units",
      "fixture_reference":"REJECT_ENTITY_ROLE_MISMATCH",
      "observed_e1":res,
      "finding":"UNITS_AND_GENERIC_PERSON_TYPE_CANNOT_REPLACE_ENTITY_SEMANTICS"})
    return result

def main():
    results=p1_cases()
    out=HERE/"output";out.mkdir(exist_ok=True)
    payload={"status":"P1_BOUNDARIES_OBSERVED_NOT_LINTER_PASS",
      "stage":"P1_LIMIT_TEST_NOT_P2_IMPLEMENTATION",
      "engine":"E1 baseline, untouched",
      "n":len(results),
      "new_verified_limit_count":sum(x["case"] in ("POS-01","NEG-02","NEG-04_SUPPLEMENTAL") for x in results),
      "e1_regressions":"RUN_SEPARATELY",
      "cases":results,
      "cautions":["Synthetic classes are in-memory structural fixtures, not executable Modelica molecules.",
                  "Reference conservation is only a fixture-level contract, no ODE or proof of nonnegativity.",
                  "An E1 rejection is not evidence of correct semantic diagnosis.",
                  "No LLM writes executable AST or equations.",
                  "No world hidden truth or causal validity claim."]}
    (out/"results.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
    print("P1_BOUNDARY_RESULTS",json.dumps({"status":payload["status"],
            "n":len(results),"cases":[[x["case"],x["observed_e1"]] for x in results]}))
if __name__=="__main__":main()
