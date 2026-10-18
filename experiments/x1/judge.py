#!/usr/bin/env python3
"""X1 adjudication after commitments. Report all worlds, failures and cost."""
import argparse,hashlib,json,math
from collections import Counter
from pathlib import Path

ACTIONS=("none","upgrade_preparation","upgrade_distribution")
def load(p):return json.loads(Path(p).read_text())
def main():
    p=argparse.ArgumentParser()
    for f in ("truth","initial","choices","observed","decisions","out"):
        p.add_argument("--"+f,required=True,type=Path)
    a=p.parse_args()
    truth,ini,choices,obs,decision=(load(getattr(a,n)) for n in
                                    ("truth","initial","choices","observed","decisions"))
    canonical=json.dumps({"world_by_case":truth["world_by_case"]},sort_keys=True,separators=(",",":"))
    sha=hashlib.sha256((truth["private_salt"]+canonical).encode()).hexdigest()
    if len({sha,ini["seal_sha256"],choices["seal_sha256"],obs["seal_sha256"],decision["seal_sha256"]})!=1:
        raise RuntimeError("UNSEALED_OR_ALTERED_TRUTH")
    worlds=truth["world_by_case"]
    routes={}
    records=[]
    for case in ini["cases"]:
        cid=case["id"];real=worlds[cid]
        optimal=max(ACTIONS,key=lambda act:truth["candidates"][real]["actions"][act]["net_units"])
        theoretical=truth["candidates"][real]["actions"][optimal]["net_units"]
        rows={}
        for arm in ("A","B","C"):
            selected=choices["choices"][cid][arm]["probe"]
            observed=obs["cases"][cid][arm]
            resp=decision["cases"][cid][arm]
            if selected!=observed["probe"] or selected!=resp["probe"]:
                raise RuntimeError("PROBE_COMMITMENT_CHANGED")
            if selected is not None and selected not in case["allowed_probes"]:
                raise RuntimeError("UNAUTHORIZED_PROBE")
            if resp["observation"]!=observed["value"]:
                raise RuntimeError("OBSERVATION_FABRICATION")
            if selected is not None:
                expected=truth["candidates"][real]["observables"][selected]
                if abs(observed["value"]-expected)>1e-9:
                    raise RuntimeError("OBSERVATION_NOT_FROM_TRUTH")
            choice=resp["action"]
            if choice not in (*ACTIONS,"abstain"):
                raise RuntimeError("INVALID_ACTION")
            realized_action=choice if choice!="abstain" else "none"
            probe_cost=ini["probes"][selected]["cost"] if selected else 0.0
            pay=truth["candidates"][real]["actions"][realized_action]
            value=pay["net_units"]-probe_cost
            regret=theoretical-value
            interval=resp["predicted_deliveries_8h"]
            coverage=(interval is not None and interval[0]-1e-5<=pay["delivery_by_8h"]<=interval[1]+1e-5)
            compatible=real in resp["surviving_hypotheses"]
            rows[arm]={"choice":choice,"actual_world":real,"best_possible_action":optimal,
                "net_value_after_probe_cost":value,"regret_vs_omniscient":regret,
                "probe":selected,"probe_cost":probe_cost,
                "actual_deliveries_8h":pay["delivery_by_8h"],
                "committed_interval_covers_heldout":coverage,
                "true_world_retained":compatible,
                "abstained":choice=="abstain",
                "admitted_model_output":resp.get("admission") if arm=="C" else "N_A"}
            records.append({"case":cid,"arm":arm,**rows[arm]})
        routes[cid]=rows
    summaries={}
    for arm in ("A","B","C"):
        subset=[r for r in records if r["arm"]==arm]
        summaries[arm]={
            "n":len(subset),
            "total_regret":sum(r["regret_vs_omniscient"] for r in subset),
            "mean_regret":sum(r["regret_vs_omniscient"] for r in subset)/len(subset),
            "right_decision":sum(r["choice"]==r["best_possible_action"] for r in subset),
            "justified_abstentions":sum(r["abstained"] for r in subset),
            "false_exclusion_of_true_world":sum(not r["true_world_retained"] for r in subset),
            "heldout_prediction_coverage":sum(r["committed_interval_covers_heldout"] for r in subset),
            "total_probe_cost":sum(r["probe_cost"] for r in subset),
            "model_valid_outputs":sum(r["admitted_model_output"]=="VALID" for r in subset) if arm=="C" else None,
        }
    mechanisms=Counter(worlds.values())
    # This is not a victory gate. If the run accidentally has only one world,
    # indicate that the cross-mechanism design was not realized.
    result={
      "status":"X1_SINGLE_INTEGRATED_RUN_RECORDED",
      "design_diversity":"TWO_DIFFERENT_TRUE_WORLDS_PRESENT" if len(mechanisms)==2 else "INCONCLUSIVE_ONLY_ONE_TRUE_WORLD",
      "nature":"Ideal, noise-free, same model family for all candidates and oracle",
      "seal_sha256":sha,"opened_private_salt_after_commitments":truth["private_salt"],
      "world_by_case_revealed_after_decisions":worlds,
      "summary":summaries,
      "incremental_C_over_B_regret_reduction":summaries["B"]["total_regret"]-summaries["C"]["total_regret"],
      "incremental_C_over_A_regret_reduction":summaries["A"]["total_regret"]-summaries["C"]["total_regret"],
      "cases":routes,
      "cautions":[
        "Models and evaluator use the same registered Modelica mechanisms, so in-universe prediction validity is expected, not evidence of discovery.",
        "No claim of real-world profitability or out-of-distribution performance.",
        "Do not claim AI value unless C beats a competitive B at equal budget and cost.",
        "Abstention is accounted as no investment, not treated as a free correct decision.",
        "One tiny idealized experiment cannot establish statistical superiority."
      ]
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("X1_FINAL_SCORE",json.dumps({
        "diversity":result["design_diversity"],
        "summary":summaries,
        "incremental_C_over_B":result["incremental_C_over_B_regret_reduction"]}))
if __name__=="__main__":main()
