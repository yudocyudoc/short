#!/usr/bin/env python3
"""Execute C0 A/B with Cloudflare Workers AI; isolated prompts, bounded spend.

The model sees only scenario + shared instructions + selected arm. Never load
evaluation/reference.md or expose credentials in logs. Run under workflow_dispatch.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
C0 = ROOT / "experiments" / "c0"
OUT = ROOT / "c0-cloudflare-results"
OUT.mkdir(exist_ok=True)
ACCOUNT = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
MODEL = os.getenv("C0_CF_MODEL", "@cf/zai-org/glm-4.7-flash")
ORDER = [x.strip().upper() for x in os.getenv("C0_RUN_ORDER", "A,B").split(",") if x.strip()]
MAX_TOKENS = min(3000, max(100, int(os.getenv("C0_MAX_COMPLETION_TOKENS", "2400"))))
if not ACCOUNT or not TOKEN:
    raise SystemExit("Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN in Actions secrets")
if not ORDER or len(ORDER) > 2 or any(x not in {"A", "B"} for x in ORDER):
    raise SystemExit("C0_RUN_ORDER must contain one or two arms A/B")
if MODEL != "@cf/zai-org/glm-4.7-flash":
    raise SystemExit("Only the pinned @cf/zai-org/glm-4.7-flash model is allowed in C0")

scenario = (C0 / "scenario.md").read_text()
common = (C0 / "prompts" / "common.md").read_text()
arms = {a: (C0 / "prompts" / f"arm-{a.lower()}.md").read_text() for a in {"A", "B"}}

def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

metadata = {
    "date_utc": datetime.now(timezone.utc).isoformat(),
    "runner": "Cloudflare Workers AI REST (NOT former SD-AI motor)",
    "model": MODEL,
    "order": ORDER,
    "temperature": 0.1,
    "max_completion_tokens": MAX_TOKENS,
    "max_total_calls": 2,
    "scenario_sha256": sha(scenario),
    "common_sha256": sha(common),
    "arm_sha256": {a: sha(arms[a]) for a in ("A", "B")},
    "estimated_usd": 0,
    "results": [],
}

def extract(result):
    if isinstance(result, str):
        return result
    if not isinstance(result, dict):
        return ""
    if isinstance(result.get("response"), str):
        return result["response"]
    if isinstance(result.get("choices"), list) and result["choices"]:
        first = result["choices"][0]
        if isinstance(first.get("message"), dict):
            return first["message"].get("content") or ""
        return first.get("text") or ""
    return ""

url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/ai/run/{MODEL}"
for i, arm in enumerate(ORDER, 1):
    prompt = (
        "### scenario.md\n" + scenario + "\n\n"
        + "### prompts/common.md\n" + common + "\n\n"
        + f"### prompts/arm-{arm.lower()}.md\n" + arms[arm] + "\n"
    )
    request = Request(
        url,
        data=json.dumps({"messages": [{"role": "user", "content": prompt}], "max_completion_tokens": MAX_TOKENS, "temperature": 0.1, "chat_template_kwargs": {"enable_thinking": False}}).encode("utf-8"),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=150) as response:
            raw = json.load(response)
        if not raw.get("success", True):
            raise RuntimeError(f"Cloudflare returned unsuccessful response: {str(raw.get('errors', []))[:400]}")
        result = raw.get("result", raw)
        answer = extract(result)
        if not answer.strip():
            raise RuntimeError("Cloudflare returned no text; inspect raw result artifact")
        (OUT / f"run-{i}-{arm}.md").write_text(answer, encoding="utf-8")
        # Keep complete response for usage and audit, but do not save/send credentials.
        (OUT / f"run-{i}-{arm}.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
        usage = result.get("usage", raw.get("usage", {})) if isinstance(result, dict) else {}
        prompt_tokens = usage.get("prompt_tokens") if isinstance(usage, dict) else None
        completion_tokens = usage.get("completion_tokens") if isinstance(usage, dict) else None
        # Published GLM 4.7 Flash on Workers AI: $0.0605/M input, $0.40/M output.
        # This is a retail-rate ESTIMATE, NOT invoiced spend (free daily credits may apply).
        estimate = None
        if isinstance(prompt_tokens, int) and isinstance(completion_tokens, int):
            estimate = round((prompt_tokens * 0.0605 + completion_tokens * 0.4) / 1_000_000, 7)
            metadata["estimated_usd"] += estimate
        metadata["results"].append({
            "run_id": i, "arm": arm, "status": "ok", "chars": len(answer),
            "usage": usage, "estimated_usd_before_free_allowance": estimate,
        })
        print(f"=== C0_RUN {i} ARM {arm} SUCCESS CHARS {len(answer)} ===", flush=True)
        print(answer[:24000], flush=True)
        print("=== C0_RUN_END ===", flush=True)
    except HTTPError as e:
        msg = e.read().decode("utf-8", errors="replace")
        metadata["results"].append({"run_id": i, "arm": arm, "status": "http_error",
                                    "http_status": e.code, "error": msg[:600]})
        print(f"Cloudflare HTTP {e.code}: {msg[:600]}", flush=True)
        break
    except (URLError, TimeoutError, ValueError, RuntimeError) as e:
        metadata["results"].append({"run_id": i, "arm": arm, "status": "error",
                                    "error": str(e)[:600]})
        print(f"Cloudflare inference failed: {str(e)[:600]}", flush=True)
        break

metadata["estimated_usd"] = round(metadata["estimated_usd"], 7)
(OUT / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
print("=== C0_CLOUDFLARE_METADATA ===", flush=True)
print(json.dumps(metadata, ensure_ascii=False), flush=True)
if len(metadata["results"]) != len(ORDER) or any(x["status"] != "ok" for x in metadata["results"]):
    sys.exit(2)
