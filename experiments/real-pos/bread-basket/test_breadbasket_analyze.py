"""Tests with invented three-transaction fixture, not copied POS rows."""
import io, unittest
from breadbasket_analyze import build,digest,SOURCE_BLOB

FAKE=(b"Date,Time,Transaction,Item\n"
      b"2026-01-06,10:12:00,1,Coffee\n"
      b"2026-01-06,10:12:00,1,Coffee\n"
      b"2026-01-06,10:21:00,2,NONE\n"
      b"2026-01-06,10:37:00,3,Bread\n")

class TestRealPos(unittest.TestCase):
    def test_explicit_relaxation_for_local_synthetic_fixture_only(self):
        r=build(FAKE,strict=False)
        self.assertEqual(r["quality"]["counts"]["raw_item_rows"],4)
        self.assertEqual(r["quality"]["counts"]["none_rows"],1)
        self.assertEqual(r["quality"]["counts"]["non_none_item_rows"],3)
        self.assertEqual(r["quality"]["counts"]["raw_transaction_ids"],3)
        self.assertEqual(r["quality"]["counts"]["valid_transactions"],2)
        self.assertEqual(r["quality"]["counts"]["none_only_transaction_ids"],1)
        self.assertEqual(r["observed_patterns"]["total_sale_transactions"],2)
        self.assertEqual(r["observed_patterns"]["max_transactions_in_observed_hour"],2)
        self.assertEqual(r["observed_patterns"]["max_transactions_in_observed_15min"],1)
        self.assertFalse(r["sd_model_fitted"])
        self.assertFalse(r["queue_inferred"])
    def test_exact_source_required_in_production(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_BLOB_MISMATCH"):
            build(FAKE)
    def test_no_disguised_arrival(self):
        r=build(FAKE,strict=False)
        self.assertNotIn("customer arrival time",r["identifiability"]["observable"])
        self.assertIn("actual customer arrival time",r["identifiability"]["not_observable"])
    def test_no_imputed_timestamps(self):
        src=FAKE.replace(b"10:37:00",b"INVALID")
        with self.assertRaisesRegex(ValueError,"INVALID_TIMESTAMP"):
            build(src,strict=False)
    def test_no_spoofed_schema(self):
        with self.assertRaisesRegex(ValueError,"BAD_COLUMNS"):
            build(b"transaction,date,item\n1,2026-01-01,Coffee\n",strict=False)
    def test_transaction_same_id_timestamp_mismatch_fails(self):
        src=FAKE.replace(b"10:12:00,1,Coffee\n2026-01-06,10:21",
                         b"10:13:00,1,Coffee\n2026-01-06,10:21")
        with self.assertRaisesRegex(ValueError,"INCONSISTENT_TRANSACTION_TIMESTAMP"):
            build(src,strict=False)
    def test_source_digest_enforced(self):
        self.assertEqual(len(SOURCE_BLOB),40)
        self.assertNotEqual(digest(FAKE)["git_blob_sha1"],SOURCE_BLOB)

if __name__=="__main__":unittest.main()
