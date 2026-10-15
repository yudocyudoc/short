#!/usr/bin/env python3
"""POST HOC C3: strips ONLY an outer JSON Markdown fence; NEVER repairs content.

Original preregistered C3 score remains unchanged; this is an exploratory
diagnostic to distinguish transport formatting from model-structure errors.
"""
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c3_validator import load_and_validate

ROOT = Path(__file__).resolve().parents[1]
FACTS = json.loads((ROOT / "experiments/c3/evaluation/facts.json").read_text())
P = re.compile(r"^\s*```(?:json)?\s*\n(?P<body>.*)\n```\s*$", re.I | re.S)

def unwrap_fence(text):
    match = P.fullmatch(text)
    return match.group("body") if match else text

def main(folder, dest):
    src = Path(folder)
    dst = Path(dest)
    dst.mkdir(parents=True, exist_ok=True)
    summary = {"status":"POST_HOC_DIAGNOSTIC_NOT_PREREGISTERED", "original_run":38493093296,"results":[]}
    for arm, run_id in [("A",1),("B",2)]:
        path = src / f"run-{run_id}-{arm}.txt"
        if not path.is_file():
            raise FileNotFoundError(f"Original preserved output missing: {path}")
        raw = path.read_text(encoding="utf-8")
        normalized = unwrap_fence(raw)
        original = load_and_validate(raw, FACTS)
        diagnostic = load_and_validate(normalized, FACTS)
        assert original["score"] == 0 and original["status"]=="REJECT", "Original must remain as preregistered"
        result = {
            "arm":arm, "only_removed_outer_markdown_fence":raw!=normalized,
            "preregistered_original":{"score":original["score"],"status":original["status"]},
            "posthoc_diagnostic":diagnostic,
        }
        (dst/f"posthoc-{arm}.json").write_text(json.dumps(result,indent=2,ensure_ascii=False))
        print(f"POSTHOC {arm}: primary {original['score']}/10; after fence-only normalization {diagnostic['score']}/10, {diagnostic['status']}",flush=True)
        print("FAILED_GATES: "+", ".join(g["id"] for g in diagnostic["gates"] if not g["pass"]),flush=True)
        summary["results"].append(result)
    (dst/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False))
    print("=== POSTHOC_SUMMARY ===")
    print(json.dumps(summary,ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv)!=3:
        raise SystemExit("Usage: python c3_posthoc_fence_diagnostic.py original_artifact_dir destination")
    main(sys.argv[1],sys.argv[2])
