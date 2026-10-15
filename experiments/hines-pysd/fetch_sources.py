#!/usr/bin/env python3
"""Fetch Vensim originals from publisher into transient CI space, pin SHA-256."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen

URLS=("https://vensim.com/documentation/Models/Molecules/",
      "https://www.vensim.com/documentation/Models/Molecules/")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dest",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    spec=json.loads(Path(__file__).with_name("specifications_extracted.json").read_text())
    a.dest.mkdir(parents=True,exist_ok=True)
    a.out.mkdir(parents=True,exist_ok=True)
    results={}
    for name,m in spec["model_provenance"].items():
        failures=[]
        for host in URLS:
            url=host+name
            try:
                req=Request(url,headers={"User-Agent":"Hines-SD-Parity-Audit/1.0"})
                with urlopen(req,timeout=40) as f:
                    source=f.read(100000)
                digest=hashlib.sha256(source).hexdigest()
                if digest!=m["source_sha256"] or len(source)!=m["source_bytes"]:
                    failures.append({"url":url,"error":"DIGEST_MISMATCH",
                                     "sha256":digest,"bytes":len(source)})
                    continue
                (a.dest/name).write_bytes(source)
                results[name]={"status":"VERIFIED","url":url,"sha256":digest,
                               "bytes":len(source),"drive_file_id":m["drive_file_id"]}
                break
            except Exception as e:
                failures.append({"url":url,"error":type(e).__name__,
                                 "detail":str(e)[:180]})
        if name not in results:
            results[name]={"status":"SOURCE_BLOCKED","failures":failures,
                           "expected_sha256":m["source_sha256"]}
        print("ORIGINAL",name,results[name]["status"],flush=True)
    (a.out/"source_manifest.json").write_text(json.dumps({
        "provenance":"Vensim official publisher download checked against user's Drive originals",
        "source_copies_committed":False,"files":results},indent=2)+"\n")
    if any(v["status"]!="VERIFIED" for v in results.values()):
        raise SystemExit("SOURCE_BLOCKED: cannot verify all publisher originals")

if __name__=="__main__":main()
