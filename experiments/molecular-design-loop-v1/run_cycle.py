#!/usr/bin/env python3
"""Actual Llama -> molecular-graph compiler -> OpenModelica -> repair diagnostics.
No LLM equations, no numerical values in context, max five attempted proposals.
If OM backend itself is broken, fail as backend error rather than ask Llama to
invent an equation. Persist every original response and diagnostic.
"""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from compose import validate,render,load
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
MODEL="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
SYSTEM="""Eres ARQUITECTO ESTRUCTURAL de sistemas dinámicos. Tu tarea es proponer una
composición CAUSAL de moléculas documentadas; OpenModelica será el ingeniero
que compila y ejecuta las ecuaciones que YA EXISTEN en módulos verificables.
No inventes moléculas, puertos, clases, ecuaciones, coeficientes, valores,
series, restricciones numéricas ni código Modelica. No analices cifras.
Selecciona un módulo por función REAL y une flujos de igual entidad:
Order -> PreparedOrder -> DeliveredOrder. Observaciones STATE no son puertos
materiales; no debes conectarlas como FLOW. Documenta cada nodo y cada
conexión mediante la cita LITERAL contigua de al menos 12 caracteres de los
hechos suministrados, con fact_id correcto. Sé fiel a los hechos; no agregues
inventario de producto fabricado anticipadamente cuando se preparan encargos.
Responde únicamente un JSON con 3 claves exactas:
{"instances":[{"id":"identificador_minúsculas","module":"ID_DEL_CATÁLOGO","evidence":[{"fact_id":"F1","quote":"texto literal exacto"}]}],
 "links":[{"from":"instancia.puerto","to":"instancia.puerto","evidence":[{"fact_id":"F1","quote":"texto literal exacto"}]}],
 "unresolved":[]}
El compilador tipado comprobará conectores y referencias; si hay errores te
devolveremos un diagnóstico y podrás reparar sólo los componentes afectados.
NUNCA respondas con ecuaciones ni cálculos. La salida JSON es un plano, NO un
modelo matemático de autoría libre."""
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def sha(t):return hashlib.sha256(t.encode("utf-8")).hexdigest()
def prompt(history,diagnostics=None):
    case=load("case.json");cat=load("catalog.json")
    user={"problem":case,"available_structural_molecules":cat["modules"],
          "rule":"Combine available verified mechanisms, typed ports only. No numeric values or code."}
    msgs=[{"role":"system","content":SYSTEM},{"role":"user","content":json.dumps(user,ensure_ascii=False)}]
    for last,feedback in history:
        msgs.append({"role":"assistant","content":last})
        msgs.append({"role":"user","content":json.dumps({"compiler_feedback":feedback,
          "instruction":"Revise the structural proposal using only documented modules; do not provide equations."},ensure_ascii=False)})
    return msgs
def api_call(account,token,messages):
    body={"messages":messages,"temperature":0,"max_tokens":1800,"stream":False}
    req=Request("https://api.cloudflare.com/client/v4/accounts/"+account+"/ai/run/"+MODEL,
        method="POST",headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},
        data=json.dumps(body,ensure_ascii=False).encode("utf-8"))
    with urlopen(req,timeout=150) as resp:provider=json.load(resp)
    if not isinstance(provider,dict) or provider.get("success") is False:
        raise ValueError("CLOUDFLARE_PROVIDER_FAILURE")
    inner=provider.get("result",provider)
    text=inner.get("response") if isinstance(inner,dict) else None
    if not isinstance(text,str):
        choices=inner.get("choices") if isinstance(inner,dict) else None
        if choices and isinstance(choices[0].get("message",{}).get("content"),str):
            text=choices[0]["message"]["content"]
    if not isinstance(text,str):raise ValueError("NO_PROVIDER_TEXT")
    return body,provider,text
def structural_feedback(result):
    return {"stage":"IGC_TYPE_AND_EVIDENCE_CHECKER","status":result["status"],
      "issues":result["issues"],"permitted_repairs":["SELECT_REGISTERED_MOLECULE",
      "RECONNECT_TYPED_PORT","REMOVE_UNSUPPORTED_EDGE","FIX_LITERAL_EVIDENCE"],
      "no_numerical_outputs":True}
def omc_check(folder):
    workspace=os.environ.get("GITHUB_WORKSPACE","")
    temp=os.environ.get("RUNNER_TEMP","")
    if not workspace or not temp:raise ValueError("CI_DOCKER_ENV_REQUIRED")
    csv=HERE/"om_molecule_res.csv"
    if csv.exists():csv.unlink()
    args=["docker","run","--rm","-v",workspace+":/repo",
        "-w","/repo/experiments/molecular-design-loop-v1",
        "-v",temp+"/igc-om-home:/omhome","-e","HOME=/omhome",
        "-v",temp+"/igc-om-libs:/thirdparty:ro",
        "-e","OPENMODELICALIBRARY=/thirdparty/msl:/thirdparty/systemdynamics",
        "openmodelica/openmodelica:v1.26.5-minimal","omc","assemble.mos"]
    r=subprocess.run(args,text=True,capture_output=True,timeout=220,check=False)
    (folder/"omc_stdout.txt").write_text(r.stdout,encoding="utf-8")
    (folder/"omc_stderr.txt").write_text(r.stderr,encoding="utf-8")
    if r.returncode!=0 or not csv.exists() or csv.stat().st_size<100:
        return {"ok":False,"status":"OPENMODELICA_FAILED",
           "category":"C_BACKEND_COMPILE_OR_SIMULATION",
           "repairable_by_llm":False,
           "detail":"Modelica preauthored molecule or numerical backend issue. Do NOT write equations."}
    # S2 independently verified reference and fixed benchmark: no values to Llama.
    cmd=[sys.executable,str(ROOT/"experiments/openmodelica-mto-s2/verify.py"),
        "--reference-out",str(folder/"independent_euler.csv"),
        "--equations",str(HERE/"s2_reference_res.csv"),
        "--components",str(csv),
        "--report",str(folder/"parity_report.json")]
    q=subprocess.run(cmd,text=True,capture_output=True,timeout=45,check=False)
    (folder/"numeric_audit.log").write_text(q.stdout+"\n"+q.stderr,encoding="utf-8")
    if q.returncode!=0:
        return {"ok":False,"status":"DYNAMIC_VALIDATION_FAILED",
           "category":"D_BEHAVIOR_MISMATCH",
           "repairable_by_llm":True,
           "detail":"Compiled structure failed independent S2 behavioral parity/invariants. Reconsider the arrangement of molecular ports only. No numeric values will be supplied."}
    return {"ok":True,"status":"COMPILED_SIMULATED_PARITY_PASS",
      "numeric_report":str(folder/"parity_report.json"),"repairable_by_llm":False}
def run(out,execute,max_attempts):
    if not 1<=max_attempts<=5:raise ValueError("MAX_ATTEMPTS_MUST_BE_1_TO_5")
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
    if execute and not(account and token):raise SystemExit("CLOUDFLARE_CREDENTIALS_MISSING")
    history=[];seen=set()
    manifest={"experiment":"IGC_MOLECULAR_COMPOSITION_REAL_LOOP_V1",
      "model":MODEL,"max_attempts":max_attempts,
      "actual_llm":bool(execute),"attempts":[],
      "business_evidence":"Synthetic qualitative S2, no empirical enterprise observations",
      "parameter_source":"Trusted preexisting scenario, not supplied to LLM",
      "generated_equations_by_llm":0,
      "started_utc":datetime.now(timezone.utc).isoformat()}
    for ix in range(1,max_attempts+1):
        folder=out/("attempt_"+str(ix).zfill(2))
        folder.mkdir(parents=True,exist_ok=True)
        messages=prompt(history)
        save(folder/"llm_prompt.json",{"model":MODEL,"temperature":0,"max_tokens":1800,"messages":messages})
        if not execute:continue
        step={"attempt":ix,"prompt_sha256":sha(json.dumps(messages,ensure_ascii=False))}
        try:
            body,provider,raw=api_call(account,token,messages)
            save(folder/"provider_original.json",provider)
            (folder/"original_llm_response.txt").write_text(raw,encoding="utf-8")
            proposal=json.loads(raw)
            step["response_sha256"]=sha(raw)
            step["received"]=True
        except (HTTPError,URLError,TimeoutError,ValueError,TypeError,KeyError) as exc:
            step.update({"status":"PROVIDER_OR_JSON_ERROR","type":type(exc).__name__})
            feedback={"stage":"S_JSON","status":"REPAIRABLE",
                      "issues":[{"code":"S_INVALID_JSON","detail":"Return a single valid JSON object of required schema"}]}
            history.append((raw if "raw" in locals() else "{}",feedback))
            save(folder/"feedback.json",feedback)
            manifest["attempts"].append(step);save(out/"manifest.json",manifest)
            continue
        result=validate(proposal)
        save(folder/"compiler_diagnostic.json",result)
        step["structure_status"]=result["status"]
        if not result["structure_accepted"]:
            feedback=structural_feedback(result)
            save(folder/"feedback.json",feedback)
            history.append((raw,feedback))
            step["status"]="STRUCTURAL_REPAIR_REQUESTED"
        else:
            # Identical validated graphs are never re-simulated to chase a score.
            graph=sha(json.dumps(proposal,sort_keys=True))
            if graph in seen:
                step["status"]="NO_NEW_STRUCTURE"
                manifest["attempts"].append(step)
                break
            seen.add(graph)
            source=render(proposal)
            (HERE/"IGCComposed.mo").write_text(source,encoding="utf-8")
            (folder/"IGCComposed.mo").write_text(source,encoding="utf-8")
            outcome=omc_check(folder)
            save(folder/"openmodelica_diagnostic.json",outcome)
            step["status"]=outcome["status"]
            if outcome["ok"]:
                manifest["result"]="PASS_SYNTHETIC_MOLECULAR_DESIGN_LOOP"
                manifest["accepted_attempt"]=ix
                manifest["accepted_model_source"]="trusted_molecules_and_port_renderer"
                manifest["attempts"].append(step)
                break
            if outcome["repairable_by_llm"]:
                feedback={"stage":"OPENMODELICA","status":"REPAIRABLE",
                  "issues":[{"code":outcome["category"],"detail":outcome["detail"]}]}
                save(folder/"feedback.json",feedback)
                history.append((raw,feedback))
            else:
                manifest["result"]="BACKEND_FAILURE_NOT_LLM_REPAIRABLE"
                manifest["attempts"].append(step)
                break
        manifest["attempts"].append(step)
        save(out/"manifest.json",manifest)
        print("IGC_MOLECULE_ATTEMPT",json.dumps(step),flush=True)
    if not execute:
        manifest["result"]="PREPARED_ONLY_NO_MODEL_CALLS"
    else:
        manifest.setdefault("result","NO_VALID_EXECUTED_DESIGN_IN_BUDGET")
    manifest["finished_utc"]=datetime.now(timezone.utc).isoformat()
    save(out/"manifest.json",manifest)
    print("IGC_MOLECULAR_FINAL",json.dumps({"result":manifest["result"],
      "attempts":len(manifest["attempts"]),
      "accepted":manifest.get("accepted_attempt")}),flush=True)
def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--prepare-only",action="store_true")
    g.add_argument("--execute",action="store_true")
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--max-attempts",type=int,default=5)
    a=p.parse_args()
    run(a.out,a.execute,a.max_attempts)
if __name__=="__main__":main()
