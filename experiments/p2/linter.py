#!/usr/bin/env python3
"""IGC-SL P2: minimal, generic *conceptual* IR validator.

Strict separation:
- Semantic proposal / typed relations here.
- Executable AST and native Modelica stay in E1/backend and future admitted classes.
- NO generated ODEs, no fake admission of new molecules, no 'if cafe' heuristics.
- A lint result NEVER establishes causal truth or numerical conservation.
"""
import json
from collections import Counter,defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
ALLOWED_RELATIONS={"LINK","SENSE","GOVERN"}
SUPPORTED_ADAPTERS={"readonly-stock-observation":("STOCK","SIGNAL")}
INVALIDATING={
    "UNKNOWN_CLASS","UNKNOWN_NODE","UNKNOWN_PORT","BAD_DIRECTION",
    "BAD_RELATION","TYPE_MISMATCH","ENTITY_MISMATCH","UNIT_MISMATCH",
    "MATERIAL_DUPLICATION","MATERIAL_FORK_UNVERIFIED","MATERIAL_MULTIPLE_INPUTS",
    "SEMANTIC_MISMATCH","MISSING_EVIDENCE","MISSING_SEMANTIC_INTENT",
    "BAD_NATIVE_ASSUMPTION","BAD_ADAPTER","INVALID_BINDING","PARAMETER_VALUE_FORBIDDEN"
}

def read_registry(path=None):
    return json.loads(Path(path or HERE/"registry_conceptual.json").read_text())

def diagnostic(code,at,detail):
    return {"code":code,"location":at,"detail":detail}

def bind_ports(definition,instance):
    value=instance.get("binding")
    if not isinstance(value,str) or not value or not value.isidentifier():
        raise ValueError("INVALID_BINDING")
    ports={}
    for p in definition["ports"]:
        new=dict(p)
        new["entity"]=p["entity"].replace("$T",value)
        ports[new["name"]]=new
    return ports

def lint(graph,registry):
    issues=[]
    classes=registry["classes"]
    nodes=graph.get("instances",[])
    edges=graph.get("relations",[])
    if not isinstance(nodes,list) or not isinstance(edges,list):
        return {"status":"INVALID","issues":[diagnostic("IR_SCHEMA","root","instances/relations must be lists")],
                "structurally_compatible":False,"executable":False}
    ids={}
    bound={}
    for n in nodes:
        if not isinstance(n,dict) or not isinstance(n.get("id"),str):
            issues.append(diagnostic("IR_SCHEMA","instance","Malformed node"));continue
        nid=n["id"]
        if nid in ids:
            issues.append(diagnostic("DUPLICATE_ID",nid,"Nonunique identity"));continue
        ids[nid]=n
        kind=n.get("class_id")
        if kind not in classes:
            issues.append(diagnostic("UNKNOWN_CLASS",nid,str(kind)));continue
        cls=classes[kind]
        intent=n.get("intent")
        if not isinstance(intent,str) or not intent:
            issues.append(diagnostic("MISSING_SEMANTIC_INTENT",nid,"State intended function"))
        elif intent not in cls.get("supported_capabilities",[]):
            issues.append(diagnostic("SEMANTIC_MISMATCH",nid,
                    "Intent "+intent+" not supported by declared mechanism contract"))
        refs=n.get("evidence",[])
        if not refs and not n.get("hypothesis",False):
            issues.append(diagnostic("MISSING_EVIDENCE",nid,
                    "Use evidence ids or an explicit unsupported HYPOTHESIS state"))
        if any(isinstance(v,(float,int)) and type(v)!=bool for v in n.get("parameters",{}).values()):
            issues.append(diagnostic("PARAMETER_VALUE_FORBIDDEN",nid,
                                     "The conceptual layer must not invent numerical bindings"))
        try:bound[nid]=bind_ports(cls,n)
        except ValueError as ex:issues.append(diagnostic(str(ex),nid,"Entity binding required"))
    consumed=Counter()
    material_sources=defaultdict(list)
    incoming=defaultdict(list)
    touched=set()
    stock_multirate=[]
    for index,e in enumerate(edges):
        loc=f"rel[{index}]"
        if not isinstance(e,dict) or e.get("kind") not in ALLOWED_RELATIONS:
            issues.append(diagnostic("BAD_RELATION",loc,"LINK / SENSE / GOVERN only"));continue
        try:
            fromid,fromport=e["from"].split(".")
            toid,toport=e["to"].split(".")
        except (KeyError,AttributeError,ValueError):
            issues.append(diagnostic("IR_SCHEMA",loc,"Bad port reference"));continue
        if fromid not in bound or toid not in bound:
            issues.append(diagnostic("UNKNOWN_NODE",loc,"Endpoint not in admitted registry"));continue
        if fromport not in bound[fromid] or toport not in bound[toid]:
            issues.append(diagnostic("UNKNOWN_PORT",loc,"Port not declared in class"));continue
        a=bound[fromid][fromport]
        b=bound[toid][toport]
        touched.update((fromid,toid))
        if a["direction"]!="out" or b["direction"]!="in":
            issues.append(diagnostic("BAD_DIRECTION",loc,"Expected out -> in"));continue
        kind=e["kind"]
        adapter=e.get("adapter")
        if kind=="LINK" and (a["kind"],b["kind"])!=("FLOW","FLOW"):
            issues.append(diagnostic("TYPE_MISMATCH",loc,"LINK moves FLOW only"))
        if kind=="SENSE":
            if (a["kind"],b["kind"]) not in [("SIGNAL","SIGNAL"),("STOCK","SIGNAL"),("FLOW","SIGNAL")]:
                issues.append(diagnostic("TYPE_MISMATCH",loc,"SENSE cannot be material transfer"))
            if a["kind"]!="SIGNAL" and adapter!="readonly-stock-observation":
                issues.append(diagnostic("BAD_ADAPTER",loc,"Sensor adapter must be read-only, registered"))
        if kind=="GOVERN" and (a["kind"],b["kind"])!=("CONTROL","CONTROL"):
            issues.append(diagnostic("TYPE_MISMATCH",loc,"GOVERN must use CONTROL ports"))
        if adapter and adapter not in SUPPORTED_ADAPTERS:
            issues.append(diagnostic("BAD_ADAPTER",loc,"Only registered read-only adapter available"))
        if kind=="LINK" and adapter:
            issues.append(diagnostic("BAD_ADAPTER",loc,"Material transfers cannot use SENSE adapter"))
        if a["entity"]!=b["entity"] or ids[fromid].get("entity_role")!=ids[toid].get("entity_role"):
            # entity_role disallows 'Person' hiding Customer -> Employee conversion.
            issues.append(diagnostic("ENTITY_MISMATCH",loc,
                                     f"{a['entity']}/{ids[fromid].get('entity_role')} vs {b['entity']}/{ids[toid].get('entity_role')}"))
        if a["unit"]!=b["unit"]:
            # Observing STOCK<Entity> -> SIGNAL<Entity> can preserve quantity
            # units, but other dimensional conversions require a verified adapter.
            issues.append(diagnostic("UNIT_MISMATCH",loc,a["unit"]+" -> "+b["unit"]))
        if not e.get("evidence") and not e.get("hypothesis",False):
            issues.append(diagnostic("MISSING_EVIDENCE",loc,"Every relation must cite or remain explicit hypothesis"))
        if kind=="LINK":
            material_sources[(fromid,fromport)].append((toid,toport))
            incoming[(toid,toport)].append((fromid,fromport))
        consumed[(toid,toport)]+=1
    for (fromid,fromport),dests in material_sources.items():
        if len(dests)>1:
            issues.append(diagnostic("MATERIAL_DUPLICATION",fromid+"."+fromport,
                "One rate output cannot be delivered in full to multiple receivers"))
    for (toid,toport),sources in incoming.items():
        if len(sources)>1:
            issues.append(diagnostic("MATERIAL_MULTIPLE_INPUTS",toid+"."+toport,
                "Merge requires registered conservation adapter"))
    # Multi-outlet physically valid only from ports explicitly guaranteed by a
    # stock conservation schema. The schema does not establish rate equations.
    for node,ports in bound.items():
        outbound=[p for (n,p) in material_sources if n==node]
        if len(outbound)>1:
            definition=classes[ids[node]["class_id"]]
            balance=definition.get("balance",{})
            if definition.get("kind")!="stock" or any(x not in balance.get("out",[]) for x in outbound):
                issues.append(diagnostic("MATERIAL_FORK_UNVERIFIED",node,
                                         "No registered multiple-outflow stock conservation contract"))
            else:
                stock_multirate.append(node)
    for node,instance in ids.items():
        if node not in touched:
            issues.append(diagnostic("ISOLATED_INSTANCE",node,"Instance not part of tested graph"))
    required=graph.get("requested_policies",[])
    policy_missing=[]
    for name in required:
        if name not in classes or not classes[name].get("policy_native_verified",False):
            policy_missing.append(name)
    for e in edges:
        if isinstance(e,dict) and e.get("kind")=="GOVERN":
            ref=e.get("from","").split(".")[0]
            if ref not in ids or not classes[ids[ref]["class_id"]].get("policy_native_verified",False):
                policy_missing.append("unverified_govern_source:"+ref)
    if policy_missing:
        issues.append(diagnostic("POLICY_UNIMPLEMENTED","requested_policies",
              "Policy is not verified natively: "+",".join(sorted(set(policy_missing)))))
    blocking=[i for i in issues if i["code"] in INVALIDATING or i["code"] in ("DUPLICATE_ID","IR_SCHEMA","ISOLATED_INSTANCE")]
    valid=not blocking
    return {
        "status":"INVALID" if blocking else ("STRUCTURAL_WITH_MISSING_POLICY" if policy_missing else "STRUCTURAL_ONLY"),
        "issues":issues,"structurally_compatible":valid,
        "executable":False,
        "conservation":"TOPOLOGY_CONTRACT_ONLY_NOT_NUMERICALLY_VERIFIED",
        "native_class_admitted":False,
        "multi_outlet_stock_instances":stock_multirate,
        "note":"Engineering consistency only: no numeric rates, equations, solver, or causal proof."
    }
