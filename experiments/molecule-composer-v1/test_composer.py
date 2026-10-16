#!/usr/bin/env python3
"""Deterministic positive and negative tests for the Hines molecule compiler."""
import json
import unittest
from pathlib import Path
from composer import compile_selection,decode,load
from run_llm import build_prompt

ROOT=Path(__file__).resolve().parent

def sample(cid):
    return (ROOT/"samples"/(cid+".txt")).read_text(encoding="utf-8")

class CompilerTests(unittest.TestCase):
    def test_four_verified_sources_have_pinned_hashes(self):
        cat=load("catalog.json");backup=load("drive_backup_discovery.json")
        self.assertEqual(len(cat["molecules"]),4)
        self.assertEqual(len(backup["entries"]),83)
        self.assertEqual(backup["model_files"],82)
        self.assertEqual(backup["documentation_files"],1)
        self.assertEqual(sum(x["stage"]=="VERIFIED4" for x in backup["entries"]),4)
    def test_make_to_stock_compile(self):
        compiled=compile_selection("S1",sample("S1"))
        self.assertEqual(compiled["status"],"COMPILED")
        self.assertTrue(compiled["safe_to_simulate"])
        self.assertEqual(set(compiled["molecules"]),{"CAP_UTIL","BACKLOG_FLOW"})
        self.assertEqual(compiled["wires"][0]["unit"],"orders/hour")
        self.assertEqual(len(compiled["source_hashes"]),2)
    def test_mto_abstention_safe(self):
        result=compile_selection("S2",sample("S2"))
        self.assertEqual(result["status"],"ABSTAIN")
        self.assertFalse(result["safe_to_simulate"])
        self.assertIn("UNPREPARED_WORK_BACKLOG",result["reason"])
    def test_pos_abstention_safe(self):
        result=compile_selection("S3",sample("S3"))
        self.assertEqual(result["status"],"ABSTAIN")
        self.assertFalse(result["safe_to_simulate"])
        self.assertIn("UNOBSERVED",result["reason"])
    def test_reject_false_mto_reuse(self):
        result=compile_selection("S2",sample("S1"))
        self.assertEqual(result["status"],"REJECT")
        self.assertFalse(result["safe_to_simulate"])
    def test_reject_unknown_model_even_if_plausible(self):
        candidate=sample("S1").replace("CAP_UTIL, BACKLOG_FLOW","CAP_UTIL, DOING_WORK").replace(
            "CAP_UTIL.Production -> BACKLOG_FLOW.Producing","CAP_UTIL.Production -> DOING_WORK.Producing")
        result=compile_selection("S1",candidate)
        self.assertEqual(result["status"],"REJECT")
        self.assertEqual(result["reason"],"UNKNOWN_MOLECULE")
    def test_reject_missing_connection(self):
        candidate=sample("S1").replace(
            "CONEXIONES: CAP_UTIL.Production -> BACKLOG_FLOW.Producing","CONEXIONES: NINGUNA")
        result=compile_selection("S1",candidate)
        self.assertEqual(result["status"],"REJECT")
        self.assertEqual(result["reason"],"UNAUTHORIZED_OR_MISSING_CONNECTION")
    def test_reject_fabricated_port(self):
        candidate=sample("S1").replace("CAP_UTIL.Production ->","CAP_UTIL.Capacity ->")
        result=compile_selection("S1",candidate)
        self.assertEqual(result["status"],"REJECT")
    def test_reject_graph_smuggled_into_abstention(self):
        candidate=sample("S1").replace("ESTADO: ENSAMBLAR","ESTADO: ABSTENER")
        result=compile_selection("S1",candidate)
        self.assertEqual(result["status"],"REJECT")
    def test_reject_malformed_or_repeated_headers(self):
        self.assertEqual(compile_selection("S1","not a valid memo")["status"],"REJECT")
        self.assertEqual(compile_selection("S1",sample("S1")+"\nESTADO: ENSAMBLAR")["status"],"REJECT")
    def test_prompt_keeps_private_policies_out_and_sources_separate(self):
        cases=load("cases_public.json")["cases"]
        cat=load("catalog.json")
        for c in cases:
            p=build_prompt(c,cat)
            self.assertIn("INDICE DE RESPALDO EN DRIVE",p)
            self.assertIn("DoingWork.mdl",p)
            self.assertIn("CapUtil.mdl",p)
            self.assertNotIn("UNOBSERVED_ARRIVALS_CAPACITY_AND_LOST_DEMAND",p)
            self.assertNotIn("source_sha256\": \"60c403",p)
            self.assertNotIn("Drive file ID",p)
    def test_verified_molecule_names_and_sizes_in_private_backup(self):
        inv={x["filename"]:x for x in load("drive_backup_discovery.json")["entries"]}
        spec=json.loads((ROOT.parents[1]/"experiments/hines-pysd/specifications_extracted.json").read_text())
        for name,item in spec["model_provenance"].items():
            self.assertEqual(inv[name]["size_bytes"],item["source_bytes"])

if __name__=="__main__":unittest.main()
