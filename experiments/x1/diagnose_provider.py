#!/usr/bin/env python3
"""Connection-only diagnostic; NEVER reads X1 cases, truth, or scorer data."""
import json,os
from urllib.request import Request,urlopen
from urllib.error import HTTPError
model="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
account=os.environ.get("CLOUDFLARE_ACCOUNT_ID","")
token=os.environ.get("CLOUDFLARE_API_TOKEN","")
if not account or not token:
    print("PROVIDER_DIAGNOSTIC",json.dumps({"status":"NO_SECRETS"}));raise SystemExit(1)
payload={"messages":[{"role":"system","content":"Reply with a short JSON object."},
                     {"role":"user","content":"Return {\"ready\":true}."}],
         "max_tokens":80,"temperature":0,"stream":False}
req=Request("https://api.cloudflare.com/client/v4/accounts/"+account+"/ai/run/"+model,
   data=json.dumps(payload).encode(),method="POST",
   headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
try:
    with urlopen(req,timeout=60) as r:
        status=r.status
        result=json.load(r)
    body=result.get("result")
    msg={"status":"HTTP_OK","http":status,"success":result.get("success"),
         "error_codes":[x.get("code") for x in result.get("errors",[]) if isinstance(x,dict)],
         "error_types":[x.get("message","")[:100] for x in result.get("errors",[]) if isinstance(x,dict)],
         "result_type":type(body).__name__,
         "result_keys":list(body)[:20] if isinstance(body,dict) else None,
         "has_response":isinstance(body,dict) and isinstance(body.get("response"),str)}
    print("PROVIDER_DIAGNOSTIC",json.dumps(msg))
except HTTPError as err:
    raw=err.read()[:3000]
    try:
        body=json.loads(raw)
        codes=[x.get("code") for x in body.get("errors",[]) if isinstance(x,dict)]
        message=[x.get("message","")[:100] for x in body.get("errors",[]) if isinstance(x,dict)]
    except Exception:codes=[];message=["BODY_NOT_JSON"]
    print("PROVIDER_DIAGNOSTIC",json.dumps({"status":"HTTP_ERROR","code":err.code,
         "provider_codes":codes,"provider_messages":message}))
