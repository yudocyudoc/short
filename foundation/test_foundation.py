"""Non-tautological negative controls for the E0 engineering regression checker."""
import csv
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
spec = importlib.util.spec_from_file_location("check_smoke", HERE / "check_smoke.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BLOBS = {
    "IGCMolecules.mo": "2f83de72d38d0b8f5e866295b806d19067c5194d",
    "IGCInformationMolecules.mo": "36d97a7e9de4d7ee80bf884beec6094a9bb1cf98",
}
FIELDS = ["time", "acceptedRate", "physicalDeliveryRate", "waitingStock",
          "totalDelivered", "reportedDeliveryRate"]


def sample_rows(filtered):
    data = []
    for i in range(12):
        flow = 1 if i < 6 else 0.5
        data.append({"time": i, "acceptedRate": 2, "physicalDeliveryRate": flow,
                     "waitingStock": 1.0, "totalDelivered": 0.5 * i,
                     "reportedDeliveryRate": flow * 0.5 if filtered else flow})
    return data


def write_csv(file, rows):
    with Path(file).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


class FoundationTests(unittest.TestCase):
    def test_molecules_are_byte_identical_to_reviewed_sources(self):
        for name, expected in BLOBS.items():
            payload = (ROOT / "src" / "modelica" / name).read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
            self.assertEqual(actual, expected, name)

    def test_controls_pass_valid_synthetic_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.csv", Path(d) / "b.csv"
            write_csv(a, sample_rows(False))
            write_csv(b, sample_rows(True))
            result = mod.verify(a, b)
            self.assertEqual(result["technical"], "PASS")
            self.assertEqual(result["methodological"], "ENGINEERING_ONLY")

    def test_detects_nonintrusive_filter_violation(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.csv", Path(d) / "b.csv"
            bad = sample_rows(True)
            bad[5]["physicalDeliveryRate"] = 0.7
            write_csv(a, sample_rows(False))
            write_csv(b, bad)
            with self.assertRaisesRegex(ValueError, "REPORT_FILTER_CHANGED_PHYSICAL_SYSTEM"):
                mod.verify(a, b)

    def test_detects_filter_no_effect(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.csv", Path(d) / "b.csv"
            write_csv(a, sample_rows(False))
            write_csv(b, sample_rows(False))
            with self.assertRaisesRegex(ValueError, "FILTER_NO_MEASURABLE_EFFECT"):
                mod.verify(a, b)

    def test_rejects_wrong_time_alignment(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.csv", Path(d) / "b.csv"
            bad = sample_rows(True)
            bad[4]["time"] = 4.5
            write_csv(a, sample_rows(False))
            write_csv(b, bad)
            with self.assertRaisesRegex(ValueError, "TIME_GRIDS_DIFFER"):
                mod.verify(a, b)


if __name__ == "__main__":
    unittest.main()
