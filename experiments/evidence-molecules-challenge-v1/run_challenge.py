#!/usr/bin/env python3
"""Challenge continuation with EXACT frozen pilot evaluator, prompts, baseline and catalog.

No model equations, numerical settings or free Modelica from the LLM. New cases
and labels were fixed before first inference; original code is hash checked.
"""
from __future__ import annotations
import argparse,hashlib,json,math,os,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

HERE=Path(__file__).resolve().parent
PILOT=HERE.parent/"evidence-molecules-pilot-v1"
sys.path.insert(0,str(PILOT))
import evaluate as original_eval
import deterministic as original_baseline
import run_llm as original_prompt

ORIGINAL_GIT_BLOBS={
 "run_llm.py":"7ccd118871987194e597175f2aa27653e509eb8b",
 "deterministic.py":"c0ab9d8e6cfd5b1c3f28fb1081f66672e9721063",
 "evaluate.py":"23ee7d08d10834c51143e4ecde1ddfe649d5b4c9",
 "catalog_public.json":"18de84dad30a9627fc219676ae456168bd9da36f"
}
def gitblob(b:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def load(name):
    return json.loads((HERE/name).read_text(encoding="utf-8"))
def dump(path,item):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(item,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def sha(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()

def setup():
    for f,expected in ORIGINAL_GIT_BLOBS.items():
        actual=gitblob((PILOT/f).read_bytes())
        if actual!=expected:raise RuntimeError("FROZEN_PILOT_SOURCE_DRIFT:"+f)
    new_cases=load("cases_public.json")["cases"]
    new_gold=load("gold_private.json")["cases"]
    assert len(new_cases)==24 and len(new_gold)==24
    assert list(new_gold)==[c["id"] for c in new_cases]
    assert len(set(c["id"] for c in new_cases))==24
    allowed=original_eval.MOLECULES
    for case in new_cases:
        facts={f["id"]:f["text"] for f in case["facts"]}
        assert len(facts)==len(case["facts"])
        assert len(facts)>=3
        goal=new_gold[case["id"]]
        assert set(goal["molecules"])<=allowed
        assert set(goal["supported_facts"])==set(goal["molecules"])
        for mid,refs in goal["supported_facts"].items():
            assert refs and set(refs)<=set(facts)
        # Source text remains qualitatively worded.
        for text in facts.values():assert not any(ch.isdigit() for ch in text)
    # Dataset parameter injection: source modules remain byte-for-byte frozen.
    original_eval.CASES={case["id"]:case for case in new_cases}
    original_eval.GOLD=new_gold
    return new_cases

def paired_comparison(b,c):
    xb={r["case_id"]:r["strict_pass"] for r in b["individual_cases"]}
    xc={r["case_id"]:r["strict_pass"] for r in c["individual_cases"]}
    c_wins=sorted(k for k in xb if not xb[k] and xc[k])
    b_wins=sorted(k for k in xb if xb[k] and not xc[k])
    n=len(b_wins)+len(c_wins)
    two_sided=min(1.0,2*sum(math.comb(n,k) for k in range(min(len(c_wins),len(b_wins))+1))/2**n) if n else 1.0
    return {"c_wins":len(c_wins),"b_wins":len(b_wins),
            "c_winning_case_ids":c_wins,"b_winning_case_ids":b_wins,
            "discordant":n,"exact_two_sided_mcnemar_p_exploratory":two_sided,
            "c_minus_b_strict_count":c["strict_pass"]-b["strict_pass"]}

def score(responses):
    a=original_eval.summarize(responses["deterministic"],"deterministic")
    b=original_eval.summarize(responses["generic_sd"],"generic_sd")
    c=original_eval.summarize(responses["molecular_scaffold"],"molecular_scaffold")
    return {"study":"IGC_CHALLENGE_PAIRED_V1","n":24,"scores":{
          key:{k:v for k,v in rep.items() if k!="individual_cases"} for key,rep in zip(("deterministic","generic_sd","molecular_scaffold"),(a,b,c))},
          "paired_B_vs_C":paired_comparison(b,c),
          "case_details":{arm:rep["individual_cases"] for arm,rep in zip(("deterministic","generic_sd","molecular_scaffold"),(a,b,c))},
          "caution":"Exploratory: cases and reference labels devised together by same project; baseline/prompt source frozen, not third-party blind; 24 paired cases underpowered for small effects."}

def run(out,execute):
    cases=setup()
    account=os.environ.get("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=os.environ.get("CLOUDFLARE_API_TOKEN","").strip()
    if execute and not (account and token):raise SystemExit("CLOUDFLARE_SECRETS_UNAVAILABLE")
    baseline={c["id"]:original_baseline.respond(c) for c in cases}
    dump(out/"baseline_frozen_responses.json",baseline)
    base=original_eval.summarize(baseline,"deterministic")
    dump(out/"baseline_frozen_score.json",base)
    responses={"deterministic":baseline,"generic_sd":{},"molecular_scaffold":{}}
    manifest={"study":"IGC_CHALLENGE_PAIRED_V1","model":original_prompt.MODEL,
      "temperature":0,"max_tokens":1250,"total_cases":len(cases),
      "actual_llm":execute,"expected_model_calls":48,"retry_count":0,
      "frozen_original_git_blobs":ORIGINAL_GIT_BLOBS,
      "baseline_exact":base["exact_selection"],"baseline_strict":base["strict_pass"],
      "started_utc":datetime.now(timezone.utc).isoformat(),"entries":[]}
    # Change ordering across cases, no feedback from previous cases or results.
    for i,case in enumerate(cases):
        for arm in (("generic_sd","molecular_scaffold") if i%2==0
                    else ("molecular_scaffold","generic_sd")):
            cid=case["id"]
            folder=out/"actual_llm"/arm/cid
            msgs=original_prompt.messages(case,arm)
            body={"messages":msgs,"stream":False,"temperature":0,"max_tokens":1250}
            dump(folder/"request_no_secrets.json",{"model":original_prompt.MODEL,"body":body})
            entry={"case_id":cid,"arm":arm,"status":"PREPARED_ONLY",
                   "prompt_sha256":sha(json.dumps(msgs,ensure_ascii=False))}
            if execute:
                req=Request(f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{original_prompt.MODEL}",
                  method="POST",headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},
                  data=json.dumps(body).encode("utf-8"))
                try:
                    with urlopen(req,timeout=120) as handle: provider=json.load(handle)
                    dump(folder/"provider_original.json",provider)
                    raw=original_prompt.extract(provider)
                    (folder/"original.txt").write_text(raw,encoding="utf-8")
                    responses[arm][cid]=raw
                    entry.update({"status":"RECEIVED","original_sha256":sha(raw),
                                  "length":len(raw)})
                except HTTPError as exc: entry.update({"status":"HTTP_ERROR","code":exc.code})
                except (URLError,TimeoutError) as exc: entry.update({"status":"TRANSPORT_ERROR","kind":type(exc).__name__})
                except (ValueError,TypeError,KeyError,UnicodeError) as exc: entry.update({"status":"OUTPUT_ERROR","kind":type(exc).__name__})
            manifest["entries"].append(entry)
            dump(out/"manifest.json",manifest)
            print("CHALLENGE_CALL",json.dumps(entry),flush=True)
    if execute:
        for arm in ("generic_sd","molecular_scaffold"):
            dump(out/(arm+"_responses.json"),responses[arm])
        report=score(responses)
        dump(out/"challenge_report.json",report)
        manifest["paired_summary"]=report["paired_B_vs_C"]
        manifest["scores"]=report["scores"]
        manifest["received"]=sum(len(responses[k]) for k in ("generic_sd","molecular_scaffold"))
        manifest["complete"]=manifest["received"]==48
    manifest["finished_utc"]=datetime.now(timezone.utc).isoformat()
    dump(out/"manifest.json",manifest)
    print("CHALLENGE_COMPLETED",json.dumps({"received":manifest.get("received",0),
       "baseline_strict":base["strict_pass"],
       "scores":manifest.get("scores",{}),
       "paired":manifest.get("paired_summary",{})},ensure_ascii=False),flush=True)
    if execute and not manifest["complete"]:
        raise SystemExit("INCOMPLETE_48_REAL_CALLS_REPORT_SAVED")

def main():
    ap=argparse.ArgumentParser()
    m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--prepare-only",action="store_true")
    m.add_argument("--execute",action="store_true")
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    run(a.out,a.execute)
if __name__=="__main__":main()
