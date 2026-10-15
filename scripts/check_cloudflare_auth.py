#!/usr/bin/env python3
"""Validate GitHub repository Cloudflare secrets without AI inference.

Never prints secret values, token ids, or token verifier response bodies.
"""
import os, json, re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
print("has_token:",bool(token))
print("token_has_whitespace:",any(c.isspace() for c in token))
print("token_has_outer_quotes:", token[:1] in ("'", '"') or token[-1:] in ("'", '"'))
print("token_has_bearer_prefix:",token.lower().startswith("bearer "))
print("token_equals_account_id:",bool(token) and token == account)
print("token_has_placeholder_brackets:","<" in token or ">" in token)
print("has_account_id:",bool(account))
print("account_id_format_valid:",bool(re.fullmatch(r"[0-9a-fA-F]{32}",account)))
if not token:
    raise SystemExit(2)

def status(url):
    req=Request(url,headers={"Authorization":f"Bearer {token}"},method="GET")
    try:
        with urlopen(req, timeout=25) as response:
            body=json.load(response)
            return {"http":response.status,"active":body.get("result",{}).get("status")=="active",
                    "success":body.get("success",False)}
    except HTTPError as e:
        try:
            data=json.loads(e.read().decode("utf-8","replace"))
            errors=data.get("errors",[])
            sanitized=[{"code":i.get("code"),"message":str(i.get("message","")).replace(token,"***").replace(account,"***")[:160]} for i in errors[:3]]
        except Exception:
            sanitized=[]
        return {"http":e.code,"active":False,"success":False,"errors":sanitized}
    except (URLError, ValueError, TimeoutError) as e:
        return {"network_error":e.__class__.__name__,"active":False,"success":False}

user=status("https://api.cloudflare.com/client/v4/user/tokens/verify")
print("user_token_verification:",json.dumps(user))
if account and re.fullmatch(r"[0-9a-fA-F]{32}",account):
    scoped=status(f"https://api.cloudflare.com/client/v4/accounts/{account}/tokens/verify")
    print("account_token_verification:",json.dumps(scoped))
else:
    print("account_token_verification: skipped (invalid account ID format)")
print("No model inference was made. Zero AI usage by this diagnostic.")
