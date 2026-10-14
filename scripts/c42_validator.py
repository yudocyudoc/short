#!/usr/bin/env python3
"""C4.2: C4's unchanged 10 gates + independent stock-flow certificates.

No model values are repaired; coverage follows named stock IDs and flow units.
"""
from c4_validator import validate_model

TYPE_FOR_UNIT={"request":"request","beverage_equivalent":"material","beverage":"material"}

def check_stock_flow_coverage(obj):
    if not isinstance(obj,dict) or not isinstance(obj.get("stocks"),list) or not isinstance(obj.get("flows"),list):
        return {"pass":False,"reason":"Missing stocks/flows arrays", "certificates":[]}
    certificates=[]
    seen=set()
    for stock in obj["stocks"]:
        if not isinstance(stock,dict) or not all(k in stock for k in ("id","unit","initial","final")):
            return {"pass":False,"reason":"Malformed stock","certificates":certificates}
        sid=stock["id"];unit=stock["unit"];start=stock["initial"];end=stock["final"]
        if not isinstance(sid,str) or sid in seen or type(start) is not int or type(end) is not int:
            return {"pass":False,"reason":"Malformed or duplicated stock","certificates":certificates}
        seen.add(sid)
        entity=TYPE_FOR_UNIT.get(unit)
        if entity is None:
            certificates.append({"stock":sid,"pass":False,"reason":"Unknown stock unit"})
            continue
        inbound=[]
        outbound=[]
        incompatible=[]
        for flow in obj["flows"]:
            if not isinstance(flow,dict):
                return {"pass":False,"reason":"Malformed flow","certificates":certificates}
            if flow.get("to")==sid or flow.get("from")==sid:
                if (flow.get("unit")!=unit or flow.get("entity")!=entity
                        or type(flow.get("total")) is not int or flow["total"]<0):
                    incompatible.append(flow.get("id","<missing-id>"))
                elif flow.get("to")==sid:
                    inbound.append(flow)
                elif flow.get("from")==sid:
                    outbound.append(flow)
        declared_delta=end-start
        implied_delta=sum(x["total"] for x in inbound)-sum(x["total"] for x in outbound)
        has_coverage=(declared_delta==0 or bool(inbound or outbound))
        passed=not incompatible and has_coverage and declared_delta==implied_delta
        certificates.append({
            "stock":sid, "unit":unit, "start":start,"end":end,
            "declared_delta":declared_delta,"flow_delta":implied_delta,
            "inbound":[{"id":x["id"],"total":x["total"]} for x in inbound],
            "outbound":[{"id":x["id"],"total":x["total"]} for x in outbound],
            "incompatible_flow_ids":incompatible,
            "pass":passed,
            "reason":None if passed else "Stock delta lacks matching compatible incident flows"
        })
    return {"pass":bool(certificates) and all(x["pass"] for x in certificates),
            "reason":None if certificates and all(x["pass"] for x in certificates)
                     else "At least one stock change is not explained by declared flows",
            "certificates":certificates}


def evaluate(obj,facts):
    if obj is None:
        return {"status":"FORMAT_REJECT","c4_score":0,"c4_status":"REJECT",
                "p11_pass":False,"p11":{"pass":False,"reason":"No JSON object",
                "certificates":[]},"c4_gates":[]}
    c4=validate_model(obj,facts)
    ledger=check_stock_flow_coverage(obj)
    accepted=c4["status"]=="ACCEPT" and ledger["pass"]
    return {"status":"ACCEPT" if accepted else "REJECT",
            "c4_score":c4["score"],"c4_status":c4["status"],
            "p11_pass":ledger["pass"],"p11":ledger,"c4_gates":c4["gates"]}
