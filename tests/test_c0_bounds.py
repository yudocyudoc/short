"""Deterministic controls for C0; these do NOT replace AI inference."""
import unittest


def upper_bound_deliveries(hours, machine_rate, available_units):
    if any(x < 0 for x in (hours, machine_rate, available_units)):
        raise ValueError("No negative quantities in base scenario")
    return min(hours * machine_rate, available_units)


def minimum_not_delivered(requests, max_deliverable):
    return max(0, requests - max_deliverable)


class TestC0Reference(unittest.TestCase):
    def test_machine_two_hours(self):
        self.assertEqual(2 * 12, 24)

    def test_joint_upper_bound(self):
        self.assertEqual(upper_bound_deliveries(2, 12, 18), 18)

    def test_minimum_not_delivered_not_auto_pending(self):
        self.assertEqual(minimum_not_delivered(30, 18), 12)

    def test_machine_limited_counterfactual(self):
        self.assertEqual(upper_bound_deliveries(2, 12, 40), 24)

    def test_inventory_limited_counterfactual(self):
        self.assertEqual(upper_bound_deliveries(2, 100, 18), 18)

    def test_no_observed_delivery_in_reference(self):
        # Any outcome within bounds could be consistent with totals without timing
        # or acceptance observations; "18 delivered" is NOT entailed.
        self.assertTrue(all(0 <= delivered <= 18 for delivered in (0, 5, 18)))
        self.assertFalse(19 <= 18)

    def test_people_do_not_impose_unjustified_one_drink_cap(self):
        people = 10
        requests = 30
        self.assertGreater(requests, people)
        self.assertEqual(upper_bound_deliveries(2, 12, 18), 18)


if __name__ == "__main__":
    unittest.main()
