#!/usr/bin/env python3
"""Small deterministic boundary: natural-language proposal -> permitted typed Hines graph.

No generated equations, code, sources, or model parameters are accepted from the LLM.
A text proposal is an input, not a command. The compiler's decision rules are
independent of the LLM and do not assert general-purpose SD model understanding.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
HEADINGS = ("ESTADO", "MOLECULAS", "CONEXIONES", "EXPLICACION", "DATOS_FALTANTES")
LINE = re.compile(r"^([A-Z_]+)\s*:\s*(.*)$")
WIRE = re.compile(r"^([A-Z_]+)\.([A-Za-z ]+)\s*->\s*([A-Z_]+)\.([A-Za-z ]+)$")

def load(filename):
    return json.loads((ROOT / filename).read_text(encoding="utf-8"))

def decode(proposal):
    """A small header protocol with unrestricted prose; never require LLM JSON."""
    sections={}
    active=None
    for raw in proposal.splitlines():
        match=LINE.match(raw.strip())
        if match and match.group(1) in HEADINGS:
            key,value=match.groups()
            if key in sections: raise ValueError("DUPLICATED_HEADING:" + key)
            sections[key]=value.strip()
            active=key
        elif active:
            sections[active]+="\n"+raw.strip()
        elif raw.strip():
            raise ValueError("TEXT_BEFORE_HEADING")
    if any(h not in sections for h in HEADINGS):
        raise ValueError("MISSING_HEADING")
    state=sections["ESTADO"].strip().upper()
    if state not in ("ENSAMBLAR","ABSTENER"):raise ValueError("UNKNOWN_STATE")
    def items(key):
        val=sections[key].strip()
        if val.upper()=="NINGUNA":return []
        return [v.strip() for v in val.split(",") if v.strip()]
    ids=items("MOLECULAS")
    if len(ids)!=len(set(ids)):raise ValueError("DUPLICATE_MOLECULE")
    wires=[]
    for v in items("CONEXIONES"):
        m=WIRE.fullmatch(v)
        if m is None:raise ValueError("INVALID_WIRE_SYNTAX")
        wires.append((m.group(1)+"."+m.group(2),m.group(3)+"."+m.group(4)))
    if len(wires)!=len(set(wires)):raise ValueError("DUPLICATE_WIRE")
    if len(sections["EXPLICACION"].strip())<24:raise ValueError("EXPLANATION_TOO_SHORT")
    if len(sections["DATOS_FALTANTES"].strip())<10:raise ValueError("MISSING_DATA_TOO_SHORT")
    return {"state":state,"ids":ids,"wires":wires,
            "explanation":sections["EXPLICACION"].strip(),
            "missing_data":sections["DATOS_FALTANTES"].strip()}

def compile_selection(case_id,proposal,catalog=None,policies=None):
    catalog=catalog or load("catalog.json")
    policies=policies or load("compiler_policies.json")
    if case_id not in policies["cases"]:raise ValueError("UNKNOWN_CASE")
    requirement=policies["cases"][case_id]
    try:parsed=decode(proposal)
    except ValueError as exc:
        return {"case_id":case_id,"status":"REJECT","reason":str(exc),
                "safe_to_simulate":False}
    ids=parsed["ids"]
    allowed={m["id"]:m for m in catalog["molecules"]}
    invalid=sorted(set(ids)-set(allowed))
    if invalid:
        return {"case_id":case_id,"status":"REJECT","reason":"UNKNOWN_MOLECULE",
                "ids":invalid,"safe_to_simulate":False}
    if parsed["state"]=="ABSTENER":
        if ids or parsed["wires"]:
            return {"case_id":case_id,"status":"REJECT",
                    "reason":"ABSTENTION_MUST_NOT_CONTAIN_EXECUTABLE_GRAPH",
                    "safe_to_simulate":False}
        return {"case_id":case_id,"status":"ABSTAIN",
                "reason":"NO_APPROVED_COMPOSITION" if requirement["may_execute"]
                         else requirement["blocking_reason"],
                "safe_to_simulate":False,"explanation":parsed["explanation"],
                "missing_data":parsed["missing_data"]}
    if not requirement["may_execute"]:
        return {"case_id":case_id,"status":"REJECT",
                "reason":"UNSUPPORTED_OPERATIONAL_CONTRACT:"+requirement["blocking_reason"],
                "safe_to_simulate":False}
    expected=set(requirement["required_molecules"])
    if set(ids)!=expected or len(ids)!=len(expected):
        return {"case_id":case_id,"status":"REJECT","reason":"MISSING_OR_EXTRA_MOLECULE",
                "safe_to_simulate":False}
    if set(map(tuple,parsed["wires"]))!=set(map(tuple,requirement["required_connections"])):
        return {"case_id":case_id,"status":"REJECT","reason":"UNAUTHORIZED_OR_MISSING_CONNECTION",
                "safe_to_simulate":False}
    for src,dst in parsed["wires"]:
        from_id,from_port=src.split(".",1)
        to_id,to_port=dst.split(".",1)
        source=allowed[from_id];sink=allowed[to_id]
        if from_port not in source["outputs"] or to_port not in sink["inputs"]:
            return {"case_id":case_id,"status":"REJECT","reason":"PORT_DOES_NOT_EXIST",
                    "safe_to_simulate":False}
        if source["outputs"][from_port]!=sink["inputs"][to_port]:
            return {"case_id":case_id,"status":"REJECT","reason":"UNITS_MISMATCH",
                    "safe_to_simulate":False}
    # Trust only allowlisted filenames in the pinned source-provenance manifest.
    manifest=json.loads((REPO/"experiments/hines-pysd/specifications_extracted.json").read_text())
    hashes={}
    for mid in sorted(expected):
        name=allowed[mid]["file"]
        if name not in manifest["model_provenance"]:raise ValueError("UNVERIFIED_SOURCE_IN_CATALOG")
        hashes[mid]={"filename":name,
                     "source_sha256":manifest["model_provenance"][name]["source_sha256"]}
    return {"case_id":case_id,"status":"COMPILED","safe_to_simulate":True,
            "molecules":sorted(expected),
            "wires":[{"from":a,"to":b,"unit":allowed[a.split(".")[0]]["outputs"][a.split(".")[1]]}
                     for a,b in parsed["wires"]],
            "source_hashes":hashes,
            "scenario":requirement["source_simulation"],
            "field_assumptions":"SYNTHETIC_EXPLICIT",
            "explanation":parsed["explanation"],"missing_data":parsed["missing_data"]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--case",choices=["S1","S2","S3"],required=True)
    ap.add_argument("--proposal",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    result=compile_selection(args.case,args.proposal.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(args.case,result["status"],result["reason"] if "reason" in result else "HINES_COMPOSITION_READY")

if __name__=="__main__":main()
