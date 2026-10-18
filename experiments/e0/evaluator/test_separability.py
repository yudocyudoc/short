"""Evaluator controls: do not classify expected labels; read numerical series."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("e0_separation",HERE/"separability.py")
sep=importlib.util.module_from_spec(spec);spec.loader.exec_module(sep)
spec2=importlib.util.spec_from_file_location("e0_batch",HERE/"make_batch.py")
batch=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(batch)
PROTO=json.loads((HERE.parent/"protocol.json").read_text(encoding="utf-8"))


def dummy(shift=0.0):
    return [{"time":float(t),"dispatchRate":2.0,"deliveryRate":float(t)+shift,
             "inTransit":0.1,"reportedDeliveryRate":float(t)+shift}
            for t in range(110)]


class NumericComparatorTests(unittest.TestCase):
    def test_public_reference_grid_derived_from_declared_protocol(self):
        cases=list(batch.experiments(PROTO))
        self.assertEqual(len(cases),48)
        self.assertEqual(len({x["name"] for x in cases}),48)
        self.assertEqual({x["probe"] for x in cases},
                         {x["id"] for x in PROTO["interventions"]})

    def test_numeric_separation_can_fail_when_signals_equal(self):
        same=sep.compare(dummy(0),dummy(0),["deliveryRate"])
        different=sep.compare(dummy(0),dummy(0.2),["deliveryRate"])
        self.assertEqual(sep.classify(same,1e-5),"UNRESOLVED_WITHIN_OPERATIONAL_BOUND")
        self.assertEqual(sep.classify(different,1e-5),"SEPARABLE_NUMERICALLY")
        self.assertAlmostEqual(different["max_abs_difference"],0.2)

    def test_only_visible_profile_fields_count(self):
        # Physical difference must not be inferred from a perfectly matching Q observation.
        a=dummy();b=copy.deepcopy(a)
        for r in b:r["deliveryRate"]+=100
        self.assertEqual(sep.classify(sep.compare(a,b,["reportedDeliveryRate"]),1e-5),
                         "UNRESOLVED_WITHIN_OPERATIONAL_BOUND")
        self.assertEqual(sep.classify(sep.compare(a,b,["deliveryRate"]),1e-5),
                         "SEPARABLE_NUMERICALLY")

    def test_refuses_unaligned_time(self):
        a=dummy();b=dummy();b[15]["time"]=15.5
        with self.assertRaisesRegex(ValueError,"UNALIGNED_TIME_GRIDS"):
            sep.compare(a,b,["reportedDeliveryRate"])

    def test_unequal_csv_is_not_auto_aligned(self):
        a=dummy();b=dummy()[:-1]
        with self.assertRaisesRegex(ValueError,"INCOMPATIBLE_GRIDS"):
            sep.compare(a,b,["deliveryRate"])

    def test_evaluator_is_not_a_hidden_world(self):
        src=(HERE/"separability.py").read_text(encoding="utf-8")
        self.assertIn('"world_identification":"NOT_RUN"',src)
        self.assertNotIn("truth.json",src)
        self.assertNotIn("gold.json",src)


if __name__=="__main__":
    unittest.main()
