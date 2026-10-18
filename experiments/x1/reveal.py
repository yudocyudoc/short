#!/usr/bin/env python3
"""Private evaluator reads sealed truth; returns only the selected measurement."""
import argparse,hashlib,json
from pathlib import Path

def load(p):return json.loads(Path(p).read_text())
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--truth",type=Path,required=True)
    ap.add_argument("--initial",type=Path,required=True)
    ap.add_argument("--choices",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    truth=load(a.truth);initial=load(a.initial);choices=load(a.choices)
    manifest=json.dumps({"world_by_case":truth["world_by_case"]},sort_keys=True,separators=(",",":"))
    seal=hashlib.sha256((truth["private_salt"]+manifest).encode()).hexdigest()
    if seal!=initial["seal_sha256"] or seal!=choices["seal_sha256"]:
        raise RuntimeError("WORLD_SEAL_MISMATCH")
    out={}
    for case in initial["cases"]:
        cid=case["id"];world=truth["world_by_case"][cid]
        by_arm={}
        for arm in ("A","B","C"):
            probe=choices["choices"][cid][arm]["probe"]
            if probe is not None and probe not in case["allowed_probes"]:
                raise RuntimeError("UNAUTHORIZED_PROBE:"+cid)
            value=truth["candidates"][world]["observables"][probe] if probe else None
            by_arm[arm]={"probe":probe,"value":value}
        out[cid]=by_arm
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps({"stage":"OBSERVATION_ONLY_NO_TRUTH",
        "seal_sha256":seal,"cases":out},indent=2)+"\n")
    print("X1_PROBE_RESPONSES",len(out),
          "truth hidden; one optional measurement per arm")
if __name__=="__main__":main()
