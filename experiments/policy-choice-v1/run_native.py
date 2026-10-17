#!/usr/bin/env python3
"""Run each DISTINCT selected architecture in OpenModelica, not synthetic scored gold.
No LLM equations. Reuses preexisting S1/S2 library implementations."""
from __future__ import annotations
import argparse,json,os,subprocess
from pathlib import Path
from compose import validate,render
HERE=Path(__file__).resolve().parent
def save(p,x):
    p.parent.mkdir(exist_ok=True,parents=True)
    p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--responses",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    manifest=json.loads(a.responses.read_text(encoding="utf-8"))["results"]
    workspace=os.environ.get("GITHUB_WORKSPACE")
    tmp=os.environ.get("RUNNER_TEMP")
    if not workspace or not tmp:raise SystemExit("GITHUB_OM_DOCKER_REQUIRED")
    a.out.mkdir(parents=True,exist_ok=True)
    modules={}
    attribution={}
    for cid,item in manifest.items():
        proposal=item.get("accepted_proposal")
        if not proposal:attribution[cid]="NO_ACCEPTED_PROPOSAL";continue
        v=validate(cid,proposal)
        if not v["executable"]:
            attribution[cid]=v["status"];continue
        kind=v["chosen_policy"]
        if kind not in modules:
            source=render(cid,proposal)
            (HERE/"IGCSelected.mo").write_text(source,encoding="utf-8")
            csv=HERE/"policy_candidate_res.csv"
            if csv.exists():csv.unlink()
            cmd=["docker","run","--rm","-v",workspace+":/repo",
              "-w","/repo/experiments/policy-choice-v1",
              "-v",tmp+"/igc-choice-home:/omhome","-e","HOME=/omhome",
              "-v",tmp+"/igc-choice-libs:/thirdparty:ro",
              "-e","OPENMODELICALIBRARY=/thirdparty/msl:/thirdparty/systemdynamics",
              "openmodelica/openmodelica:v1.26.5-minimal","omc","candidate.mos"]
            proc=subprocess.run(cmd,text=True,capture_output=True,timeout=180)
            (a.out/(kind+"_omc_stdout.log")).write_text(proc.stdout,encoding="utf-8")
            (a.out/(kind+"_omc_stderr.log")).write_text(proc.stderr,encoding="utf-8")
            (a.out/(kind+"_IGCSelected.mo")).write_text(source,encoding="utf-8")
            success=proc.returncode==0 and csv.exists() and csv.stat().st_size>100
            if success:
                (a.out/(kind+"_res.csv")).write_bytes(csv.read_bytes())
            modules[kind]={"status":"OMC_PASS" if success else "OMC_FAILED",
               "generated_by":"trusted native model template, not LLM equations",
               "result_csv":kind+"_res.csv" if success else None}
        attribution[cid]=modules[kind]["status"]
    result={"compiled_alternatives":modules,"case_native_results":attribution,
      "note":"Each unique selected policy was compiled and executed in OpenModelica, using preauthored native S1/S2. The separate zero-orders experiment tests behavioral contrast; this execution alone is NOT empirical fit."}
    save(a.out/"native_report.json",result)
    print("POLICY_NATIVE",json.dumps(result,ensure_ascii=False),flush=True)
    if any(v["status"]!="OMC_PASS" for v in modules.values()):raise SystemExit("MODEL_EXECUTION_FAILURE")
if __name__=="__main__":main()
