#!/usr/bin/env python3
"""C0 A/B isolated inference harness using GitHub Copilot CLI.

Each inference receives only scenario + common + arm; reference files are NEVER
put in the prompt. Model runs with no tools in a fresh temporary working dir.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
C0=ROOT/"experiments"/"c0"
OUT=ROOT/"c0-run-output"
OUT.mkdir(exist_ok=True)
MODEL=os.getenv("C0_MODEL","gpt-4.1")
ORDER=["A","B","B","A","A","B"]
scenario=(C0/"scenario.md").read_text()
common=(C0/"prompts"/"common.md").read_text()
arms={a:(C0/"prompts"/("arm-"+a.lower()+".md")).read_text() for a in ("A","B")}

metadata={"date_utc":datetime.now(timezone.utc).isoformat(),"model_requested":MODEL,
          "runner":"GitHub Copilot CLI (NOT original SD-AI motor)","order":ORDER,
          "context":"fresh CLI per call; no tools; only three source docs",
          "temperature":"Copilot CLI default, not explicitly controlled",
          "scenario_sha256":hashlib.sha256(scenario.encode()).hexdigest(),
          "common_sha256":hashlib.sha256(common.encode()).hexdigest(),
          "arm_sha256":{a:hashlib.sha256(arms[a].encode()).hexdigest() for a in arms},
          "results":[]}

for i,arm in enumerate(ORDER,1):
    prompt="### scenario.md\n"+scenario+"\n\n### prompts/common.md\n"+common+"\n\n### prompts/arm-"+arm.lower()+".md\n"+arms[arm]+"\n"
    with tempfile.TemporaryDirectory(prefix="c0-isolated-") as directory:
        env=os.environ.copy()
        # Copilot cannot use repository tools: CLI -p noninteractive without allow-tool.
        try:
            result=subprocess.run(["copilot","-p",prompt,"-s","--no-ask-user","--model",MODEL],
                cwd=directory,env=env,text=True,capture_output=True,timeout=180)
        except Exception as ex:
            result=None
            (OUT/f"run-{i}-{arm}.error.txt").write_text(str(ex))
            metadata["results"].append({"run_id":i,"arm":arm,"status":"exception","message":str(ex)[:300]})
            break
    output=result.stdout
    (OUT/f"run-{i}-{arm}.md").write_text(output)
    (OUT/f"run-{i}-{arm}.stderr.txt").write_text(result.stderr)
    info={"run_id":i,"arm":arm,"returncode":result.returncode,"chars":len(output),
          "status":"ok" if result.returncode==0 and len(output.strip())>50 else "failure"}
    metadata["results"].append(info)
    print(f"=== C0_RUN {i} ARM {arm} EXIT {result.returncode} CHARS {len(output)} ===",flush=True)
    print(output[:22000],flush=True)
    print("=== C0_RUN_END ===",flush=True)
    if info["status"]!="ok":
        print("Failure tail: "+result.stderr[-1500:],flush=True)
        break
(OUT/"metadata.json").write_text(json.dumps(metadata,indent=2,ensure_ascii=False))
print("=== C0_RUN_METADATA ===",flush=True)
print(json.dumps(metadata,ensure_ascii=False),flush=True)
if len(metadata["results"]) != len(ORDER) or any(r["status"]!="ok" for r in metadata["results"]):
    sys.exit(2)
