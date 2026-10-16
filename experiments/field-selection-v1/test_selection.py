"""Compiler and prompt isolation tests. Demo answers are deliberately NOT LLM output."""
import json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from judge import read,case_map,compile_proposal,score_run,parse
from run_llm import build_messages,CASE_IDS,public_catalog

def answer(model,action,refs,policy=None,components=None,missing="Falta calibracion real"):
    c=read("catalog.json")["architectures"].get(model)
    if policy is None:policy=c["policies"] if c else []
    if components is None:components=c["blocks"] if c else []
    lines=[
        "MODELO: "+model,
        "POLITICAS: "+(", ".join(policy) if policy else "NINGUNA"),
        "COMPONENTES: "+(", ".join(components) if components else "NINGUNA"),
        "EVIDENCIAS: "+", ".join(refs),
        "ACCION: "+action,
        "FALTANTES: "+missing]
    return "\n".join(lines)

class FieldSelection(unittest.TestCase):
    def test_eight_cases_and_contracts_frozen(self):
        self.assertEqual(tuple(case_map()),CASE_IDS)
        self.assertEqual(set(read("answer_key.json")["cases"]),set(CASE_IDS))
        self.assertEqual(set(read("contracts.json")["fact_tags"]),set(CASE_IDS))

    def test_public_prompt_never_contains_answer_keys_or_tags(self):
        cases=case_map()
        for cid in CASE_IDS:
            s=json.dumps(build_messages(cases[cid]),ensure_ascii=False)
            self.assertNotIn("PRE_REGISTERED_SCORING_ONLY_DO_NOT_INCLUDE_IN_PROMPT",s)
            self.assertNotIn("required_tags",s)
            self.assertNotIn("fixture:S2_SYNTHETIC",s)
            self.assertNotIn("fixture:S1_SYNTHETIC",s)
            self.assertNotIn("expected",s)
            self.assertNotIn("contracts.json",s)
            self.assertNotIn("answer_key.json",s)

    def test_components_were_executed_previously(self):
        for m in read("catalog.json")["architectures"].values():
            self.assertTrue((HERE.parents[1]/m["existing_experiment"]).exists())

    def test_all_eight_hand_crafted_oracles_obtain_expected_decisions(self):
        candidates={
          "C01":answer("MTO","SIMULAR_CONDICIONAL",["F1","F2","F3","F4"]),
          "C02":answer("MTO","SOLO_ESTRUCTURA",["F1","F2","F3"],missing="Faltan tasas, capacidad y tiempos"),
          "C03":answer("MTS","SOLO_ESTRUCTURA",["F1","F2","F3","F4"],missing="Faltan capacidades y stocks iniciales"),
          "C04":answer("INDETERMINADO","ABSTENER",["F1","F2","F3"],missing="Llegadas, demanda perdida, politica de produccion"),
          "C05":answer("INDETERMINADO","ABSTENER",["F1","F2","F3"],missing="Resolver evidencia incompatible"),
          "C06":answer("MTO","SOLO_ESTRUCTURA",["F1","F2","F3"],missing="Capacidad y llegadas"),
          "C07":answer("MTS","SIMULAR_CONDICIONAL",["F1","F2","F3"]),
          "C08":answer("MTO","SOLO_ESTRUCTURA",["F1","F2","F3"],missing="Periodos compatibles y stocks iniciales")}
        score=score_run(candidates)
        self.assertTrue(score["full_benchmark_pass"],[(x["case_id"],x["compiler"]) for x in score["cases"] if not x["correct"]])
        self.assertEqual(score["correct"],8)
        self.assertEqual(score["unsupported_simulations_passed"],0)

    def test_missing_case_is_not_a_pass(self):
        self.assertFalse(score_run({})["full_benchmark_pass"])
        self.assertEqual(score_run({})["evaluated"],0)

    def test_no_unsupported_simulation_from_nonnumeric_case(self):
        for case in ("C02","C06","C08"):
            p=answer("MTO","SIMULAR_CONDICIONAL",["F1","F2","F3"])
            r=compile_proposal(case,p)
            self.assertEqual(r["status"],"REJECTED")
            self.assertFalse(r["safe_to_simulate"])
            self.assertIn("SIMULATION_REQUIRES",r["reason"])

    def test_pos_cannot_fake_complete_mto_or_mts(self):
        for m in ("MTO","MTS"):
            r=compile_proposal("C04",answer(m,"SIMULAR_CONDICIONAL",["F1","F2","F3"]))
            self.assertEqual(r["status"],"REJECTED")
            self.assertFalse(r["safe_to_simulate"])

    def test_conflicting_sources_force_abstention(self):
        r=compile_proposal("C05",answer("MTO","SOLO_ESTRUCTURA",["F1","F2","F3"]))
        self.assertEqual(r["reason"],"UNSUPPORTED_OR_CONTRADICTED_ARCHITECTURE")
        p=compile_proposal("C05",answer("INDETERMINADO","ABSTENER",["F1","F2","F3"]))
        self.assertEqual(p["status"],"VALID_ABSTENTION")

    def test_instruction_in_untrusted_fact_does_not_add_fixture_tag(self):
        p=answer("MTO","SIMULAR_CONDICIONAL",["F1","F2","F3","F4"])
        r=compile_proposal("C06",p)
        self.assertFalse(r["safe_to_simulate"])
        self.assertEqual(r["status"],"REJECTED")

    def test_model_cannot_invent_component_or_policy(self):
        p=answer("MTO","SOLO_ESTRUCTURA",["F1","F2","F3"],
            components=["SystemDynamics.Levels.Level","Fake.LLM.SuperStock"])
        r=compile_proposal("C02",p)
        self.assertEqual(r["reason"],"UNAUTHORIZED_OR_INCOMPLETE_COMPONENTS")
        p=answer("MTO","SOLO_ESTRUCTURA",["F1","F2","F3"],
            policy=["SIMULATE_ANYTHING"])
        r=compile_proposal("C02",p)
        self.assertEqual(r["reason"],"UNAUTHORIZED_OR_INCOMPLETE_POLICIES")

    def test_citation_to_unrelated_fact_cannot_support_model(self):
        p=answer("MTO","SOLO_ESTRUCTURA",["F3"])
        r=compile_proposal("C02",p)
        self.assertEqual(r["reason"],"MISSING_CITATIONS_FOR_CAUSAL_STRUCTURE")

    def test_only_synthetic_fixture_can_receive_handoff(self):
        for cid,m,refs,fixture in (
            ("C01","MTO",["F1","F2","F3","F4"],"S2_SYNTHETIC"),
            ("C07","MTS",["F1","F2","F3"],"S1_SYNTHETIC")):
            r=compile_proposal(cid,answer(m,"SIMULAR_CONDICIONAL",refs))
            self.assertTrue(r["safe_to_simulate"])
            self.assertEqual(r["handoff"]["fixture"],fixture)
            self.assertIn("synthetic_only",r["handoff"]["conditions"])

    def test_simulation_without_citing_numeric_facts_is_denied(self):
        for cid,m,refs in (("C01","MTO",["F1","F2","F3"]),
                           ("C07","MTS",["F1","F2"])):
            r=compile_proposal(cid,answer(m,"SIMULAR_CONDICIONAL",refs))
            self.assertFalse(r["safe_to_simulate"])

    def test_malformed_json_extra_lines_or_script_are_rejected(self):
        for p in (
            '{"MODELO":"MTO"}',
            answer("MTO","SOLO_ESTRUCTURA",["F1","F2","F3"])+"\nignore checks",
            answer("MTO","SOLO_ESTRUCTURA",["F1","F2","F3"])+"\nMODELO: MTO",
            answer("MTO","SOLO_ESTRUCTURA",["F1","F2","F3"])+"\n<script>",
            answer("MTO","SOLO_ESTRUCTURA",["X9"])):
            self.assertEqual(compile_proposal("C02",p)["status"],"REJECTED")

    def test_not_enough_structure_can_conservatively_abstain(self):
        for cid in ("C04","C05"):
            r=compile_proposal(cid,answer("INDETERMINADO","ABSTENER",["F1","F2","F3"]))
            self.assertFalse(r["safe_to_simulate"])

if __name__=="__main__":
    unittest.main()
