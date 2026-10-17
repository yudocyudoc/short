#!/usr/bin/env python3
"""Offline contract tests; GitHub Actions separately runs real OpenModelica CSVs."""
import csv, json, math, tempfile, unittest
from pathlib import Path
from observability import (HERE,NAMES,PAIRS,SIGNALS,STATUS,read,validate_manifest,
    contrast,convert_signatures,measurements,evaluate_case,run,select_measurement,
    critic_case)

SIGNATURES={
 "OBSERVED_VS_DISPATCH":{"Direct":"SYNC","TransitOnly":"LAG","ReportOnly":"LAG","TransitAndReport":"LAG"},
 "PHYSICAL_VS_DISPATCH":{"Direct":"SYNC","TransitOnly":"LAG","ReportOnly":"SYNC","TransitAndReport":"LAG"},
 "OBSERVED_VS_PHYSICAL":{"Direct":"SYNC","TransitOnly":"SYNC","ReportOnly":"LAG","TransitAndReport":"LAG"}}
SIG={t:{g:("SYNC" if s=="SYNC" else "DISTINCT") for g,s in groups.items()}
     for t,groups in SIGNATURES.items()}
class ObservabilityTests(unittest.TestCase):
    def setUp(self):
        self.cases=read(HERE/"cases.json")["cases"]
        self.truth=read(HERE/"truth.json")["truth"]
    def test_predeclared_cases_separate_truth(self):
        self.assertEqual(len(self.cases),12)
        validate_manifest(self.cases,self.truth)
        self.assertFalse(any("truth" in c or "reference_model" in c for c in self.cases))
        self.assertEqual(set(self.truth.values()),set(NAMES))
    def test_signature_conversion_does_not_call_numeric_difference_lag(self):
        sig=convert_signatures({"status":"PASS","all_four_joint_signatures_distinct":True,
                                "signatures":SIGNATURES})
        self.assertEqual(sig,SIG)
        self.assertNotIn("LAG",str(sig))
        with self.assertRaises(ValueError):
            convert_signatures({"status":"UNVERIFIED","signatures":SIGNATURES})
    def test_abs_difference_is_distinct_not_time_lag(self):
        base={"unit":"orders/time_unit","source_id":"a","time_grid_id":"x",
              "n":3,"values":[1.,2.,3.]}
        other={**base,"source_id":"b","values":[2.,4.,6.]}
        self.assertEqual(contrast(base,other)[0],"DISTINCT")
        self.assertEqual(contrast(base,{**base,"source_id":"b"})[0],"SYNC")
    def test_same_source_and_wrong_units_block_comparison(self):
        base={"unit":"orders/time_unit","source_id":"a","time_grid_id":"x",
              "n":3,"values":[1.,2.,3.]}
        self.assertEqual(contrast(base,{**base,"unit":"orders","source_id":"b"})[0],"UNKNOWN")
        self.assertEqual(contrast(base,base)[1],"NONINDEPENDENT_CHANNELS")
        self.assertEqual(contrast(base,{**base,"time_grid_id":"y","source_id":"b"})[0],"UNKNOWN")
    def test_claims_never_enter_pruning(self):
        # O01 says 'transport' but measured delivery dashboard equals dispatch.
        c=self.cases[0]
        self.assertIn("transporte",c["claims"][0]["text"])
        result=evaluate_case(c,self.truth[c["id"]],self.fixture_dir(),SIG)
        self.assertEqual(result["survivors_measured_only"],["Direct"])
        self.assertTrue(result["document_claims_not_used_as_hard_constraints"])
    def fixture_dir(self):
        if not hasattr(self,"_tmp"):
            self._tmp=tempfile.TemporaryDirectory()
            self.addCleanup(self._tmp.cleanup)
            root=Path(self._tmp.name)
            for name in NAMES:
                with (root/("pulse_"+name+"_res.csv")).open("w",newline="") as f:
                    w=csv.writer(f)
                    w.writerow(["time","dispatchRate","deliveryRate","reportedDeliveryRate"])
                    for i in range(65):
                        d=1+math.sin(i/8)
                        physical=d if "Transit" not in name or name=="ReportOnly" else 1+math.sin(max(0,i-5)/8)
                        report=physical if name in ("Direct","TransitOnly") else 1+math.sin(max(0,i-(10 if name=="TransitAndReport" else 5))/8)
                        w.writerow([i/8,d,physical,report])
            self._folder=root
        return self._folder
    def test_full_offline_synthetic_campaign(self):
        folder=self.fixture_dir()
        results=[evaluate_case(c,self.truth[c["id"]],folder,SIG) for c in self.cases]
        self.assertEqual(len(results),12)
        self.assertFalse(any(x["false_elimination"] for x in results))
        byid={x["case_id"]:x for x in results}
        for cid in ("O01","O04","O07","O08"):
            self.assertEqual(len(byid[cid]["survivors_measured_only"]),1,cid)
        for cid in ("O02","O03","O06","O10"):
            self.assertEqual(len(byid[cid]["survivors_measured_only"]),3,cid)
        self.assertEqual(len(byid["O05"]["survivors_measured_only"]),4)
        self.assertEqual(len(byid["O09"]["survivors_measured_only"]),2)
        self.assertEqual(len(byid["O11"]["survivors_measured_only"]),2)
        self.assertEqual(len(byid["O12"]["survivors_measured_only"]),2)
        self.assertEqual(byid["O09"]["known_contrasts"]["OBSERVED_VS_DISPATCH"],"UNKNOWN")
        self.assertEqual(byid["O09"]["diagnostics"]["OBSERVED_VS_DISPATCH"]["obstacle"],
                         "INCOMPATIBLE_UNITS")
        self.assertIsNotNone(byid["O05"]["next_measurement"])
        self.assertTrue(all(x["provenance"]=="SIMULADO_NOT_REAL_COMPANY" for x in results))
    def test_pretend_no_measurements_cannot_eliminate(self):
        root=self.fixture_dir()
        case={**self.cases[0],"available_signals":[]}
        result=evaluate_case(case,"Direct",root,SIG)
        self.assertEqual(len(result["survivors_measured_only"]),4)
    def test_next_measurement_requires_budget_and_feasible_channel(self):
        c={**self.cases[5],"measurement_budget":0}
        result=evaluate_case(c,"TransitAndReport",self.fixture_dir(),SIG)
        self.assertIsNone(result["next_measurement"])
        c={**self.cases[5],"obtainable_signals":["dispatchRate","reportedDeliveryRate"]}
        result=evaluate_case(c,"TransitAndReport",self.fixture_dir(),SIG)
        self.assertIsNone(result["next_measurement"])
    def test_critic_input_has_no_truth_and_declares_simulated(self):
        case=self.cases[9]
        result=evaluate_case(case,self.truth[case["id"]],self.fixture_dir(),SIG)
        packet=critic_case(case,result)
        self.assertEqual(packet["id"],"O10")
        self.assertFalse(any("truth" in f or "reference_model" in f for f in packet["facts"]))
        self.assertTrue(any(f["kind"]=="SIMULATED_COMPARISON" for f in packet["facts"]))
        self.assertTrue(any(f["kind"]=="UNVERIFIED_DOCUMENT" for f in packet["facts"]))
    def test_end_to_end_writes_machine_auditable_score(self):
        temp=self.fixture_dir()
        probe=Path(temp)/"probe.json"
        probe.write_text(json.dumps({"status":"PASS","signatures":SIGNATURES,
                                     "all_four_joint_signatures_distinct":True}))
        out=Path(temp)/"result"
        summary=run(temp,probe,out)
        self.assertEqual(summary["false_eliminations"],0)
        self.assertEqual(summary["cases"],12)
        self.assertEqual(read(out/"llama_status.json")["status"],"NOT_RUN")
        self.assertEqual(len(read(out/"critic_inputs_no_truth.json")),12)
    def test_invalid_case_masks_and_hidden_truth_fail(self):
        c={**self.cases[0],"available_signals":["dispatchRate","dispatchRate"]}
        with self.assertRaises(ValueError):validate_manifest([c],{"O01":"Direct"})
        c={**self.cases[0],"unit_overrides":{"deliveryRate":"orders"}}
        with self.assertRaises(ValueError):validate_manifest([c],{"O01":"Direct"})

if __name__=="__main__":unittest.main()
