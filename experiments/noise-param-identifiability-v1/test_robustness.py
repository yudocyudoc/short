#!/usr/bin/env python3
"""Offline regression and negative controls; real OMC campaign runs in Actions."""
import math,tempfile,unittest
from pathlib import Path
from robustness import (case_specs,truth_index,time_aligned_rates,make_observations,
    compare_channels,classify_observations,validate_packet,score,DT,BOUND,CONDITIONS)
from observability import PAIRS
SIG={
 "OBSERVED_VS_DISPATCH":{"Direct":"SYNC","TransitOnly":"DISTINCT","ReportOnly":"DISTINCT","TransitAndReport":"DISTINCT"},
 "PHYSICAL_VS_DISPATCH":{"Direct":"SYNC","TransitOnly":"DISTINCT","ReportOnly":"SYNC","TransitAndReport":"DISTINCT"},
 "OBSERVED_VS_PHYSICAL":{"Direct":"SYNC","TransitOnly":"SYNC","ReportOnly":"DISTINCT","TransitAndReport":"DISTINCT"}}
def series(graph):
    points=[]
    for tick in range(65):
        d=4+2*math.sin(tick/8)
        physical=d if graph in ("Direct","ReportOnly") else 4+2*math.sin(max(0,tick-8)/8)
        rep=physical if graph in ("Direct","TransitOnly") else 4+2*math.sin(max(0,tick-12)/8)
        points.append({"time":tick*DT,"dispatchRate":d,"deliveryRate":physical,
                       "reportedDeliveryRate":rep})
    return points
def clean_channel(vals,source="source",error=0.0,quality="CALIBRATED"):
    return {"values_by_tick":{str(i):v for i,v in enumerate(vals)},
            "unit":"orders/hour","channel":source,"quality":quality,
            "certified_abs_error_bound":error if quality=="CALIBRATED" else None,
            "provenance":"SIMULATED","calibration_claim":"ASSUMED_FOR_BENCHMARK"}
class StressTests(unittest.TestCase):
    def test_frozen_cases_are_forty_and_truth_separate(self):
        specs=case_specs();truth=truth_index()
        self.assertEqual(len(specs),40)
        self.assertEqual(len({x["id"] for x in specs}),40)
        self.assertEqual(set(truth),{x["id"] for x in specs})
        self.assertFalse(any("graph" in x or "world" in x for x in specs))
        self.assertEqual(set(x["condition"] for x in specs),set(CONDITIONS))
    def test_seeded_noise_never_exceeds_certified_bound(self):
        case=next(c for c in case_specs() if c["condition"]=="BOUNDED_ALL")
        obs=make_observations(case,series("Direct"))
        for name,c in obs["channels"].items():
            originals=[r[name] for r in series("Direct")]
            self.assertTrue(all(abs(v-originals[int(i)])<=BOUND+1e-8
                for i,v in c["values_by_tick"].items()))
        self.assertEqual(obs,make_observations(case,series("Direct")))
    def test_equal_mechanism_not_falsely_discarded_by_bounded_noise(self):
        case=next(c for c in case_specs() if c["condition"]=="BOUNDED_ALL")
        obs=make_observations(case,series("Direct"))
        naive=classify_observations(obs,SIG,"naive")
        bounded=classify_observations(obs,SIG,"bounded")
        self.assertNotIn("Direct",naive["survivors"])
        self.assertIn("Direct",bounded["survivors"])
        self.assertEqual(len(bounded["survivors"]),4)
    def test_identifiable_difference_excludes_only_exact_equal_graphs(self):
        case=next(c for c in case_specs() if c["condition"]=="CLEAN_ALL")
        obs=make_observations(case,series("TransitAndReport"))
        result=classify_observations(obs,SIG,"bounded")
        self.assertEqual(result["survivors"],["TransitAndReport"])
    def test_bounded_agreement_not_proof_of_same_mechanism(self):
        equal=clean_channel([1.,1.,1.,1.,1.,1.,1.,1.],"a",0.03)
        other=clean_channel([1.,1.,1.,1.,1.,1.,1.,1.],"b",0.03)
        self.assertEqual(compare_channels(equal,other,"bounded")["status"],"INCONCLUSIVE")
        self.assertEqual(compare_channels(equal,other,"naive")["status"],"SYNC")
    def test_non_overlap_leads_to_unknown(self):
        a=clean_channel([1]*10,"a",0.03)
        b=clean_channel([1]*10,"b",0.03)
        b["values_by_tick"]={str(x+11):1 for x in range(10)}
        self.assertEqual(compare_channels(a,b,"bounded")["status"],"UNKNOWN")
    def test_invalid_calibration_not_used_by_bounded_guard(self):
        case=next(c for c in case_specs() if c["condition"]=="BAD_CALIBRATION")
        obs=make_observations(case,series("Direct"))
        self.assertEqual(obs["channels"]["reportedDeliveryRate"]["quality"],"UNCALIBRATED_GAIN")
        robust=classify_observations(obs,SIG,"bounded")
        naive=classify_observations(obs,SIG,"naive")
        self.assertIn("Direct",robust["survivors"])
        self.assertNotIn("Direct",naive["survivors"])
        self.assertEqual(robust["checks"]["OBSERVED_VS_PHYSICAL"]["status"],"INCONCLUSIVE")
    def test_missing_receipt_limits_identification(self):
        case=next(c for c in case_specs() if c["condition"]=="MISSING_RECEIPT")
        obs=make_observations(case,series("TransitOnly"))
        self.assertNotIn("deliveryRate",obs["channels"])
        kept=classify_observations(obs,SIG,"bounded")["survivors"]
        self.assertIn("TransitOnly",kept)
        self.assertGreater(len(kept),1)
    def test_sparse_independent_packets_and_no_imputation(self):
        case=next(c for c in case_specs() if c["condition"]=="SPARSE_ALL")
        obs=make_observations(case,series("ReportOnly"))
        self.assertTrue(any(len(c["values_by_tick"])<65 for c in obs["channels"].values()))
        self.assertTrue(any(len(c["values_by_tick"])>8 for c in obs["channels"].values()))
        self.assertIn("ReportOnly",classify_observations(obs,SIG,"bounded")["survivors"])
    def test_nonfinite_samples_and_unbounded_calibration_rejected(self):
        case=next(c for c in case_specs() if c["condition"]=="CLEAN_ALL")
        obs=make_observations(case,series("Direct"))
        obs["channels"]["dispatchRate"]["values_by_tick"]["0"]=float("nan")
        with self.assertRaises(ValueError):validate_packet(obs)
        obs=make_observations(case,series("Direct"))
        obs["channels"]["dispatchRate"]["certified_abs_error_bound"]=None
        with self.assertRaises(ValueError):validate_packet(obs)
    def test_duplicate_om_times_use_last_regular_sample(self):
        table=series("Direct")
        point={**table[2],"time":table[2]["time"],"dispatchRate":12.0}
        table.insert(3,point)
        self.assertEqual(time_aligned_rates(table)[2]["dispatchRate"],12.0)
        with self.assertRaises(ValueError):
            time_aligned_rates(table[:30])
    def test_classify_has_no_truth_argument(self):
        import inspect
        p=inspect.signature(classify_observations)
        self.assertEqual(list(p.parameters),["packet","signatures","mode"])
    def test_source_alias_cannot_be_treated_as_two_independent_sensors(self):
        obs=make_observations(case_specs()[0],series("Direct"))
        obs["channels"]["deliveryRate"]["channel"]="dispatch-erp"
        with self.assertRaises(ValueError):validate_packet(obs)

if __name__=="__main__":unittest.main()
