#!/usr/bin/env python3
"""Read-only model catalog check. Does not invoke Workers AI inference."""
from __future__ import annotations
import json,os,re
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from prepare import MODELS

def check(env=None,sender=urlopen):
    env=os.environ if env is None else env
    account=env.get("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=env.get("CLOUDFLARE_API_TOKEN","").strip()
    if not re.fullmatch(r"[a-fA-F0-9]{32}",account) or not token:
        raise SystemExit("Missing or malformed Cloudflare secrets. No inference made.")
    results={}
    for model in MODELS.values():
        url=("https://api.cloudflare.com/client/v4/accounts/"+account+"/ai/models/search?"+
             urlencode({"search":model}))
        try:
            with sender(Request(url,headers={"Authorization":"Bearer "+token,"Accept":"application/json"}),timeout=30) as response:
                obj=json.load(response)
            if not obj.get("success"):raise RuntimeError("Model lookup unsuccessful")
            present=model.lower().removeprefix("@cf/") in json.dumps(obj.get("result",[])).lower()
            results[model]=present
        except (HTTPError,URLError,TimeoutError,ValueError,RuntimeError) as e:
            raise SystemExit("Preflight failed: "+type(e).__name__+". No inference made.") from None
    print(json.dumps({"model_catalog":results,"inference_made":False},indent=2))
    if not all(results.values()):
        raise SystemExit("A requested model is not listed. No inference made.")
    return results
if __name__=="__main__":
    check()
