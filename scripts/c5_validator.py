#!/usr/bin/env python3
"""C5 library: 11 preregistered deterministic checks; no semantic auto-repair."""
from c42_transport import separate

NAMES=["T1_SCHEMA","T2_STOCKS","T3_FLOW_TYPES","T4_TOPOLOGY","T5_PHYSICAL_COUNTS",
       "T6_RESERVATION_COUNTS","T7_STOCK_BALANCES","T8_TOTAL_CONSERVATION",
       "T9_NO_DOUBLE_COUNT","T10_EPISTEMIC","T11_COVERAGE"]
U={"copy":"copy","reservation":"reservation"}
STOCK_FIELDS={"id","unit","initial","final"}
FLOW_FIELDS={"id","entity","from","to","total","unit"}
ROOT_FIELDS={"stocks","flows","feedback","unknowns"}

def quantity(x):
    return type(x) is int and x>=0

def certificate(model):
    cert=[]
    if not isinstance(model,dict) or not isinstance(model.get("stocks"),list) or not isinstance(model.get("flows"),list):
        return {"pass":False,"certificates":[]}
    for s in model["stocks"]:
        if not isinstance(s,dict) or not STOCK_FIELDS.issubset(s):
            return {"pass":False,"certificates":cert}
        incoming=[];outgoing=[];invalid=[]
        for f in model["flows"]:
            if not isinstance(f,dict):
                return {"pass":False,"certificates":cert}
            touches = f.get("from")==s["id"] or f.get("to")==s["id"]
            if not touches:continue
            if (f.get("entity")!=U.get(s["unit"]) or f.get("unit")!=s["unit"]
                    or not quantity(f.get("total"))):
                invalid.append(f.get("id","unknown"))
            elif f.get("from")==f.get("to"):
                invalid.append(f.get("id","self-loop"))
            elif f.get("to")==s["id"]:
                incoming.append(f)
            else:
                outgoing.append(f)
        actual=s["final"]-s["initial"]
        predicted=sum(f["total"] for f in incoming)-sum(f["total"] for f in outgoing)
        valid=(not invalid and actual==predicted and
               (actual==0 or bool(incoming or outgoing)))
        cert.append({"stock":s["id"],"unit":s["unit"],"declared_delta":actual,
                     "flow_delta":predicted,"incoming":[f["id"] for f in incoming],
                     "outgoing":[f["id"] for f in outgoing],
                     "invalid_incident_flows":invalid,"pass":valid})
    return {"pass":len(cert)>0 and all(x["pass"] for x in cert),
            "certificates":cert}

def validate(obj,facts):
    gates={name:False for name in NAMES}
    why={}
    def check(name,ok,message):
        gates[name]=bool(ok)
        if not ok:why[name]=message
    if not isinstance(obj,dict) or set(obj)!=ROOT_FIELDS:
        check("T1_SCHEMA",False,"Root object must have stocks, flows, feedback, unknowns")
        return report(gates,why,{"pass":False,"certificates":[]})
    stocks=obj["stocks"];flows=obj["flows"];feedback=obj["feedback"];unknowns=obj["unknowns"]
    stocks_valid=(isinstance(stocks,list) and all(
        isinstance(s,dict) and set(s)==STOCK_FIELDS
        and isinstance(s["id"],str) and bool(s["id"])
        and isinstance(s["unit"],str) and quantity(s["initial"]) and quantity(s["final"])
        for s in stocks))
    flows_valid=(isinstance(flows,list) and all(
        isinstance(f,dict) and set(f)==FLOW_FIELDS
        and all(isinstance(f[k],str) and bool(f[k]) for k in ("id","entity","from","to","unit"))
        and quantity(f["total"]) for f in flows))
    feedback_valid=isinstance(feedback,list) and all(
        isinstance(f,dict) and set(f)=={"name","status","justification"}
        and all(isinstance(f[k],str) for k in f) for f in feedback)
    unknowns_valid=isinstance(unknowns,list) and all(isinstance(t,str) for t in unknowns)
    check("T1_SCHEMA",stocks_valid and flows_valid and feedback_valid and unknowns_valid,
          "Malformed stock, flow, feedback or unknowns")
    if not gates["T1_SCHEMA"]:
        return report(gates,why,{"pass":False,"certificates":[]})
    wanted=facts["stock_initial"]
    units=facts["stock_unit"]
    stockmap={s["id"]:s for s in stocks}
    check("T2_STOCKS",len(stocks)==len(wanted) and len(stockmap)==len(stocks)
          and set(stockmap)==set(wanted)
          and all(stockmap[k]["initial"]==v and stockmap[k]["unit"]==units[k] for k,v in wanted.items()),
          "Expected physical and reservation stocks, units and observed initial values")
    key=lambda x:(x["from"],x["to"],x["entity"],x["unit"])
    expected={key(f):f["total"] for f in facts["observed_flows"]}
    keys=[key(f) for f in flows]
    check("T3_FLOW_TYPES",len(flows)==len(expected) and len({f["id"] for f in flows})==len(flows)
          and all(f["entity"] in U and f["unit"]==U.get(f["entity"]) for f in flows),
          "Expected nine unique copy/reservation flows with compatible entity and units")
    check("T4_TOPOLOGY",len(keys)==len(expected) and len(set(keys))==len(keys)
          and set(keys)==set(expected),
          "Wrong, missing or duplicated physical/reservation transition")
    amounts={key(f):f["total"] for f in flows}
    copy_expected={k:v for k,v in expected.items() if k[2]=="copy"}
    hold_expected={k:v for k,v in expected.items() if k[2]=="reservation"}
    check("T5_PHYSICAL_COUNTS",all(amounts.get(k)==v for k,v in copy_expected.items())
          and len([f for f in flows if f["entity"]=="copy"])==len(copy_expected),
          "Physical transfer totals differ from observation")
    check("T6_RESERVATION_COUNTS",all(amounts.get(k)==v for k,v in hold_expected.items())
          and len([f for f in flows if f["entity"]=="reservation"])==len(hold_expected),
          "Reservation creation/service/cancellation totals incorrect")
    c=certificate(obj)
    # Close every stock twice: using proposed incident flows and independent observed events.
    independent={}
    for sid,start in wanted.items():
        inc=sum(f["total"] for f in facts["observed_flows"] if f["to"]==sid)
        out=sum(f["total"] for f in facts["observed_flows"] if f["from"]==sid)
        independent[sid]=start+inc-out
    check("T7_STOCK_BALANCES",len(stockmap)==len(wanted)
          and all(sid in stockmap and stockmap[sid]["final"]==end for sid,end in independent.items())
          and c["pass"],
          "One or more closing stocks contradict observed events or declared incident flows")
    physical=["available_copies","loaned_copies","repair_copies"]
    total=sum(stockmap[s]["final"] for s in physical if s in stockmap)
    check("T8_TOTAL_CONSERVATION",len(stockmap)==len(wanted)
          and total==facts["physical_initial"]+facts["physical_inflow"]-facts["physical_outflow"]
          and total==67,
          "Total physical copies must conserve external acquisitions and retirements")
    s=facts["served_reservations"];loan=facts["loan_count"]
    loan_key=("available_copies","loaned_copies","copy","copy")
    served_key=("pending_reservations","served","reservation","reservation")
    check("T9_NO_DOUBLE_COUNT",gates["T4_TOPOLOGY"]
          and s<=loan
          and amounts.get(loan_key)==loan
          and amounts.get(served_key)==s,
          "Served reservations must be included in, not added to, physical checkouts")
    check("T10_EPISTEMIC",bool(unknowns) and all(x.strip() for x in unknowns)
          and all(f["status"]=="hypothesis" and f["name"].strip() and f["justification"].strip()
                  for f in feedback),
          "Unobserved feedback cannot be asserted; unknown timing/causes must remain uncertain")
    check("T11_COVERAGE",c["pass"] and len(c["certificates"])==len(stocks),
          "At least one stock change lacks compatible incident flows")
    return report(gates,why,c)

def report(passed,why,c):
    return {"status":"ACCEPT" if all(passed.values()) else "REJECT",
            "score":sum(passed.values()),"maximum":len(NAMES),
            "gates":[{"id":x,"pass":bool(passed[x]),"reason":None if passed[x] else why.get(x,"Dependency unavailable")} for x in NAMES],
            "stock_flow_certificate":c}

def validate_provider(value,facts):
    obj,reasoning,transport=separate(value)
    if not transport["ok"]:
        return None,reasoning,transport,{"status":"FORMAT_REJECT","score":0,"maximum":len(NAMES),
          "gates":[{"id":x,"pass":False,"reason":"Format rejected"} for x in NAMES],
          "stock_flow_certificate":{"pass":False,"certificates":[]}}
    return obj,reasoning,transport,validate(obj,facts)
