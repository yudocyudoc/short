#!/usr/bin/env python3
"""IGC0 v3 preregistered negative tests: graph gate and conditional contrast call."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/"src"))
from prepare import read_public,summarize,sha
from igc_split_gate import graph_gate,contrast_gate
from run_split_igc import execute

def packet():
    return summarize(read_public(HERE/"inputs"/"IGC0_8_mundos_analista.zip")["M01"])

def sample_graph(p):
    first=p["source_ledger"][0]
    obs={"source_id":first["source_id"],"sha256":first["sha256"]}
    ini=p["operating_reference"]["initial_conditions"]
    def ref(k):
        t=ini[k]
        return {"source_id":t["source_id"],"sha256":t["sha256"]}
    return {
        "case_id":"M01",
        "stocks":[
            {"id":"pending","unit":"orders","initial":None,"initial_label":"DESCONOCIDO","initial_refs":[]},
            {"id":"ingredients","unit":"meals_equivalent","initial":ini["inventory_meals"]["value"],
             "initial_label":"CALIBRADO","initial_refs":[ref("inventory_meals")]},
            {"id":"cash","unit":"MXN","initial":ini["cash_mxn"]["value"],
             "initial_label":"CALIBRADO","initial_refs":[ref("cash_mxn")]},
        ],
        "pipes":[
            {"id":"admit_orders","from":"external_requests","to":"pending",
             "unit_per_time":"orders/window","capacity_source":None,
             "mechanism":"aceptación de solicitudes","evidence_refs":[obs],"epistemic":"OBSERVADO"},
            {"id":"service_orders","from":"pending","to":"completed_orders",
             "unit_per_time":"orders/hour","capacity_source":None,
             "mechanism":"atención de pedidos","evidence_refs":[],"epistemic":"HIPÓTESIS"},
            {"id":"material_use","from":"ingredients","to":"used_ingredients",
             "unit_per_time":"meals_equivalent/day","capacity_source":None,
             "mechanism":"consumo de insumos","evidence_refs":[],"epistemic":"HIPÓTESIS"},
            {"id":"cash_in","from":"external_cash","to":"cash",
             "unit_per_time":"MXN/day","capacity_source":None,
             "mechanism":"cobros","evidence_refs":[],"epistemic":"HIPÓTESIS"},
        ],
        "informational_links":[
            {"from":"ingredients","to":"service_orders","type":"information","why":"disponibilidad de insumos regula pedidos"}
        ],
        "boundary":{"inside":["inventario","operación de pedidos","caja"],
                    "outside":["demanda potencial","proveedores"],
                    "possible_omissions":["despacho","carga externa de cocina"]},
        "mechanism_checks":[
            {"role":role,"status":"unknown","linked_ids":[],"evidence_refs":[],
             "explanation":"El paquete agregado no discrimina mecanismo real"}
            for role in ("shared_kitchen","order_backlog","delivery_dispatch","payout_delay")
        ],
        "unknowns":["Tiempos individuales de cola no disponibles"]
    }

def sample_contrast(p,g):
    pos=p["source_ledger"][0]
    ref=p["operating_reference"]["reference"]["kitchen_capacity_per_hour"]
    return {"case_id":"M01","graph_sha256":sha(g),
        "contrast":[{"pipe_or_mechanism_id":"service_orders","type":"possible_difference",
            "evidence_refs":[{"source_id":pos["source_id"],"sha256":pos["sha256"]},
                             {"source_id":ref["source_id"],"sha256":ref["sha256"]}],
            "epistemic":"HIPÓTESIS",
            "explanation":"La referencia especifica capacidad; el POS registra resultados por cohorte, no confirma capacidad real"}],
        "identifiability":{"status":"insufficient_data","rival_mechanisms":[],
            "discriminating_measurement":"marca temporal por cocina y despacho"},
        "actions":["no_delivery","open_full","open_offpeak_capped"],
        "decision":{"choice":"abstain","reason":"Sin motor SD calibrado","assumptions":[]},
        "scenario_projections":[],"unknowns":["No se observan tiempos de cocina individuales"]}

class TestIGC0Split(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=packet()
    def graph_bad(self,change,code):
        g=sample_graph(self.p);change(g)
        result=graph_gate(g,self.p)
        self.assertFalse(result["accepted"])
        self.assertIn(code,{x["code"] for x in result["issues"]})
    def contrast_bad(self,change,code):
        g=sample_graph(self.p);c=sample_contrast(self.p,g);change(c)
        result=contrast_gate(c,g,self.p)
        self.assertFalse(result["accepted"])
        self.assertIn(code,{x["code"] for x in result["issues"]})
    def test_positive_graph(self):
        g=sample_graph(self.p)
        result=graph_gate(g,self.p)
        self.assertTrue(result["accepted"],result["issues"])
        self.assertEqual(result["stock_count"],3)
        self.assertEqual(result["graph_sha256"],sha(g))
    def test_positive_contrast(self):
        g=sample_graph(self.p)
        result=contrast_gate(sample_contrast(self.p,g),g,self.p)
        self.assertTrue(result["accepted"],result["issues"])
    def test_graph_omits_order_stock(self):
        self.graph_bad(lambda g:g["stocks"].pop(0),"MISSING_DOMAIN_STOCK")
    def test_cross_domain_pipe(self):
        self.graph_bad(lambda g:g["pipes"].append({
            "id":"invalid","from":"ingredients","to":"cash","unit_per_time":"MXN/day",
            "capacity_source":None,"mechanism":"incorrecto","evidence_refs":[],
            "epistemic":"HIPÓTESIS"}),"CROSS_DOMAIN_STOCK_FLOW")
    def test_pipe_without_known_source(self):
        self.graph_bad(lambda g:g["pipes"][0].update(evidence_refs=[]),"UNSUPPORTED_PIPE")
    def test_initial_without_source(self):
        self.graph_bad(lambda g:g["stocks"][1].update(initial_refs=[]),"UNSUPPORTED_INITIAL")
    def test_reference_not_observed(self):
        self.graph_bad(lambda g:g["stocks"][1].update(initial_label="OBSERVADO"),"INITIAL_SOURCE_KIND")
    def test_unknown_initial_cannot_be_zero(self):
        self.graph_bad(lambda g:g["stocks"][0].update(initial=0),"UNKNOWN_INITIAL_ASSIGNED")
    def test_information_link_dangling(self):
        self.graph_bad(lambda g:g["informational_links"][0].update(to="fake"),"DANGLING_INFO_LINK")
    def test_four_roles_required(self):
        self.graph_bad(lambda g:g["mechanism_checks"].pop(),"MECHANISM_ROLES")
    def test_mechanism_no_fictive_claim(self):
        self.graph_bad(lambda g:g["mechanism_checks"][0].update(status="represented"),
                       "UNLINKED_MECHANISM")
    def test_boundary_is_explicit(self):
        self.graph_bad(lambda g:g["boundary"].update(outside=[]),"BOUNDARY")
    def test_unknowns_are_required(self):
        self.graph_bad(lambda g:g.update(unknowns=[]),"UNKNOWN_DECLARATION")
    def test_graph_does_not_accept_contrast_as_stage_one(self):
        self.graph_bad(lambda g:g.update(contrast=[]),"GRAPH_SCHEMA")
    def test_wrong_graph_hash_blocks_contrast(self):
        self.contrast_bad(lambda c:c.update(graph_sha256="0"*64),"GRAPH_HASH")
    def test_missing_observed_contrast_ref(self):
        self.contrast_bad(lambda c:c["contrast"][0].update(evidence_refs=c["contrast"][0]["evidence_refs"][1:]),
                          "CONTRAST_REFERENCES")
    def test_missing_calibrated_contrast_ref(self):
        self.contrast_bad(lambda c:c["contrast"][0].update(evidence_refs=c["contrast"][0]["evidence_refs"][:1]),
                          "CONTRAST_REFERENCES")
    def test_reject_wrong_contrast_id(self):
        self.contrast_bad(lambda c:c["contrast"][0].update(pipe_or_mechanism_id="fiction"),"UNLINKED_CONTRAST")
    def test_reject_recommendation(self):
        self.contrast_bad(lambda c:c["decision"].update(choice="open_full"),"PREMATURE_DECISION")
    def test_reject_forecast(self):
        self.contrast_bad(lambda c:c.update(scenario_projections=[{"p":22}]),"PROJECTION_NOT_ALLOWED")
    def test_gate_does_not_mutate(self):
        g=sample_graph(self.p);c=sample_contrast(self.p,g)
        gb=copy.deepcopy(g);cb=copy.deepcopy(c)
        graph_gate(g,self.p);contrast_gate(c,g,self.p)
        self.assertEqual(g,gb);self.assertEqual(c,cb)
    def test_rejected_ig_never_calls_second_stage(self):
        g=sample_graph(self.p);g["pipes"][0]["evidence_refs"]=[]
        calls=[]
        def fake_request(stage,prompt,payload,out,account,token):
            calls.append(stage)
            return g,{"api_success":True,"format":"json","usage":{}}
        with tempfile.TemporaryDirectory() as d,patch("run_split_igc.request_stage",new=fake_request):
            outcome=execute(self.p,Path(d),"dummy","dummy","graph_prompt","contrast_prompt")
            self.assertEqual(calls,["IG"])
            self.assertEqual(outcome["status"],"IG_REJECT")
            self.assertEqual(outcome["model_calls_attempted"],1)
            self.assertEqual(outcome["C_status"],"SKIPPED_IG_REJECT")
    def test_valid_ig_allows_exactly_one_contrast_call(self):
        g=sample_graph(self.p);c=sample_contrast(self.p,g)
        calls=[]
        def fake_request(stage,prompt,payload,out,account,token):
            calls.append(stage)
            return (g if stage=="IG" else c),{"api_success":True,"format":"json","usage":{}}
        with tempfile.TemporaryDirectory() as d,patch("run_split_igc.request_stage",new=fake_request):
            outcome=execute(self.p,Path(d),"dummy","dummy","graph_prompt","contrast_prompt")
            self.assertEqual(calls,["IG","C"])
            self.assertEqual(outcome["status"],"IGC_CONTRACT_ACCEPT")
            self.assertTrue((Path(d)/"combined_igc_model.json").exists())
    def test_invalid_format_stops_without_second_call(self):
        calls=[]
        def fake_request(stage,prompt,payload,out,account,token):
            calls.append(stage);return None,{"api_success":True,"format":"invalid_json"}
        with tempfile.TemporaryDirectory() as d,patch("run_split_igc.request_stage",new=fake_request):
            outcome=execute(self.p,Path(d),"dummy","dummy","graph_prompt","contrast_prompt")
            self.assertEqual(calls,["IG"])
            self.assertEqual(outcome["status"],"FORMAT_OR_PROVIDER_REJECT")
if __name__=="__main__":
    unittest.main()
