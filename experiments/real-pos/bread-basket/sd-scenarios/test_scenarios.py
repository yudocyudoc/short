"""No-source regression tests for the conditional Hines scenario adapter."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from run_scenarios import evidence_bins, ephemeral_units, series_from_counts, SOURCE_MANIFEST, ROOT


class TestConditionalSD(unittest.TestCase):
    def test_hines_manifest_remains_at_existing_location(self):
        self.assertTrue(SOURCE_MANIFEST.is_file())
        originals=json.loads(SOURCE_MANIFEST.read_text())
        self.assertIn("CapUtil.mdl",originals["model_provenance"])
        self.assertIn("invbakf.mdl",originals["model_provenance"])
    def test_precommitted_cases(self):
        config=json.loads((ROOT/"scenario_config.json").read_text())
        self.assertEqual([s["date"] for s in config["preselected_dates"]],
                         ["2017-02-04","2016-10-30"])
        self.assertEqual(config["scenario_parameters"]["hypothetical_kitchen_nominal_capacities_orders_per_hour"],
                         [8,16,32])
        self.assertEqual(config["clock"]["dt_hours"],0.25)
        self.assertEqual(config["provenance"]["llm_inference_calls"],0)
    def test_quarter_bin_not_item_row(self):
        data={"experiment":"BREAD_BASKET_OBSERVED_POS_V1",
              "source":{"git_blob_sha1":"ceea9513b75a3dda41a9209b6fd1875c12580933"},
              "observed_patterns":{
                  "transaction_counts_by_observed_15min":[
                      {"date":"2026-01-02","hour":10,"start_minute":15,"count":4},
                      {"date":"2026-01-02","hour":10,"start_minute":45,"count":2},
                      {"date":"2026-01-03","hour":10,"start_minute":15,"count":8}
                  ],
                  "transaction_counts_by_day":[{"date":"2026-01-02","count":6},
                                                {"date":"2026-01-03","count":8}]
              }}
        arr=evidence_bins(data,"2026-01-02")
        self.assertEqual(len(arr),96)
        self.assertEqual(sum(arr),6)
        self.assertEqual(arr[10*4+1],4)
        self.assertEqual(arr[10*4+3],2)
        series=series_from_counts(arr)
        self.assertEqual(len(series),97)
        self.assertEqual(series.at[10.25],16.0)
        self.assertEqual(sum(series.values[:-1]*0.25),6)
    def test_day_tally_discrepancy_blocks(self):
        data={"experiment":"BREAD_BASKET_OBSERVED_POS_V1",
              "source":{"git_blob_sha1":"ceea9513b75a3dda41a9209b6fd1875c12580933"},
              "observed_patterns":{"transaction_counts_by_observed_15min":[
                  {"date":"2026-01-02","hour":10,"start_minute":0,"count":4}],
                  "transaction_counts_by_day":[{"date":"2026-01-02","count":5}]}}
        with self.assertRaisesRegex(ValueError,"total mismatch"):
            evidence_bins(data,"2026-01-02")
    def test_unit_transformation_changes_only_labels(self):
        src=("{UTF-8}\nInventory = INTEG( Producing - Shipping , 1000 )\n"
             "\t~\tWidgets\nOrders = 1000\n\t~\tWidgets/Month\n"
             "TIME STEP=0.125\n\t~\tMonth\n").encode()
        with tempfile.TemporaryDirectory() as d:
            old=Path(d)/"orig.mdl";old.write_bytes(src)
            output=Path(d)/"adapt";output.mkdir()
            p,trace=ephemeral_units("invbakf.mdl",old,hashlib.sha256(src).hexdigest(),output)
            changed=p.read_text()
            self.assertIn("Inventory = INTEG( Producing - Shipping , 1000 )",changed)
            self.assertIn("orders/Hour",changed)
            self.assertNotIn("Widgets",changed)
            self.assertFalse(trace["model_formulas_changed"])
            with self.assertRaisesRegex(ValueError,"digest mismatch"):
                ephemeral_units("invbakf.mdl",old,"0"*64,output)
    def test_source_molecule_not_committed(self):
        self.assertFalse(any(ROOT.glob("*.mdl")))
        self.assertFalse(any(ROOT.glob("*.mdl.bin")))


if __name__=="__main__":unittest.main()
