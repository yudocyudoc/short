#!/usr/bin/env python3
"""No-inference check for secret presence, Workers AI permission, and pinned model."""
import json,os,re
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode
from urllib.request import Request,urlopen
account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip(); token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
valid=bool(re.fullmatch(r"[0-9a-fA-F]{32}",account))
print("account_secret_present:",bool(account)); print("token_secret_present:",bool(token)); print("account_id_format_valid:",valid)
if not account or not token or not valid: raise SystemExit("Preflight failed; no secrets printed; no inference made.")
url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/models/search?"+urlencode({"search":"@cf/zai-org/glm-4.7-flash"})
try:
    with urlopen(Request(url,headers={"Authorization":f"Bearer {token}","Accept":"application/json"}),timeout=30) as response:
        data=json.load(response)
        if response.status!=200 or not data.get("success"): raise SystemExit("Model search failed; no inference made.")
except HTTPError as exc:
    print("workers_ai_api_http_status:",exc.code); raise SystemExit("Preflight rejected; response body withheld.")
except (URLError,TimeoutError,ValueError) as exc:
    print("preflight_error_type:",exc.__class__.__name__); raise SystemExit("Preflight failed; no inference made.")
models=json.dumps(data.get("result",[])).lower()
found="@cf/zai-org/glm-4.7-flash" in models or "zai-org/glm-4.7-flash" in models
print("workers_ai_model_list_permission: PASS"); print("pinned_model_listed:",found); print("inference_made: false")
if not found: raise SystemExit("Pinned model not listed; no inference made.")
