#!/usr/bin/env python3
"""Independent deterministic check of the preregistered C1 observations."""
import unittest

class C1Reference(unittest.TestCase):
    def test_theoretical_capacity(self):
        self.assertEqual(12 * 2, 24)
    def test_possible_upper_bound(self):
        self.assertEqual(min(12 * 2, 18), 18)
    def test_stock_after_observed_production(self):
        self.assertEqual(18 - 13, 5)
    def test_accepted_requests_and_pending(self):
        self.assertEqual(30 - 5, 25)
        self.assertEqual(25 - 4 - 13, 8)
    def test_all_categories_exhaustive(self):
        self.assertEqual(13 + 5 + 4 + 8, 30)
    def test_cannot_equate_possible_with_actual(self):
        self.assertNotEqual(min(12*2,18), 13)
    def test_remaining_not_total_unfulfilled(self):
        self.assertEqual(30 - 13, 17)
        self.assertNotEqual(30 - 13, 8)

if __name__ == "__main__":
    unittest.main()
