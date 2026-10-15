#!/usr/bin/env python3
"""Deterministic tests for M01 wiring; no inference, no model refitting."""
import copy
import json
import unittest
from pathlib import Path

from compose_m01 import check_composition, extract
from independent_euler import lookup

HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE/"m01_composition.json").read_text())
ORIGINS = json.loads((HERE/"specifications_extracted.json").read_text())


class TestHinesM01(unittest.TestCase):
    def test_known_four_originals_and_active_three(self):
        result = check_composition(CONTRACT, ORIGINS)
        self.assertEqual(result["selected_molecules"],
                         ["backlog_shipping", "kitchen_capacity", "supplier_pipeline"])
        self.assertEqual(result["states_checked"], 6)
        self.assertEqual(result["rates_checked"], 7)

    def test_order_inventory_not_raw_ingredients(self):
        c = copy.deepcopy(CONTRACT)
        c["molecules"][0]["bindings"]["Inventory"] = "raw_ingredient_inventory"
        with self.assertRaisesRegex(ValueError, "finished-goods"):
            check_composition(c, ORIGINS)

    def test_no_cross_domain_money_food_flow(self):
        c = copy.deepcopy(CONTRACT)
        c["rates"][0]["into"] = ["cash"]
        with self.assertRaisesRegex(ValueError, "Cross-entity rate"):
            check_composition(c, ORIGINS)

    def test_rate_units_must_match_state_units(self):
        c = copy.deepcopy(CONTRACT)
        c["rates"][0]["unit"] = "meals_equivalent/hour"
        with self.assertRaisesRegex(ValueError, "Cross-entity rate"):
            check_composition(c, ORIGINS)

    def test_no_simulation_flag_required(self):
        c = copy.deepcopy(CONTRACT)
        c["execution_status"] = "SIMULATE"
        with self.assertRaisesRegex(ValueError, "safety flag"):
            check_composition(c, ORIGINS)

    def test_delay_not_mislabeled_fixed_lead(self):
        c = copy.deepcopy(CONTRACT)
        c["molecules"][2]["status"] = "CALIBRATED_FIXED_DELAY"
        with self.assertRaisesRegex(ValueError, "First-order delay"):
            check_composition(c, ORIGINS)

    def test_no_double_count_alternative_backlog(self):
        c = copy.deepcopy(CONTRACT)
        c["molecules"][3]["status"] = "REFERENCE_STRUCTURE_CANDIDATE"
        with self.assertRaises(ValueError):
            check_composition(c, ORIGINS)

    def test_original_caputil_not_hard_clamped(self):
        table = ORIGINS["models"]["CapUtil.mdl"]["lookup"]
        self.assertAlmostEqual(lookup(table, 1.4), 1.15)
        self.assertGreater(lookup(table, 1.4), 1)

    def test_missing_meal_order_conversion_is_required(self):
        c = copy.deepcopy(CONTRACT)
        c["uncertainties"] = [u for u in c["uncertainties"] if u["id"] != "meals_per_order"]
        with self.assertRaisesRegex(ValueError, "conversion"):
            check_composition(c, ORIGINS)

    def test_typed_reference_needs_complete_provenance(self):
        with self.assertRaises(ValueError):
            extract({"reference":{"capacity":{"value":16,"unit":"orders/hour"}}},
                    "reference.capacity")

    def test_unknown_stock_with_no_source_does_not_become_number(self):
        unknown = [s for s in CONTRACT["states"] if s["initial_status"] == "UNKNOWN"]
        self.assertEqual(len(unknown), 4)
        self.assertTrue(all("initial" not in s for s in unknown))


if __name__ == "__main__":
    unittest.main()
