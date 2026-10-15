#!/usr/bin/env python3
"""C2 truth-invariant controls, independent of LLM responses."""
import unittest

class C2Reference(unittest.TestCase):
    def test_machine(self): self.assertEqual(9*3,27)
    def test_maximum_joint(self): self.assertEqual(min(9*3,20),20)
    def test_inventory_balance(self): self.assertEqual(20-14,6)
    def test_accepted(self): self.assertEqual(28-6,22)
    def test_final_pending(self): self.assertEqual(22-3-14,5)
    def test_partition(self): self.assertEqual(6+3+14+5,28)
    def test_observed_not_bound(self): self.assertLess(14,20)

if __name__=="__main__": unittest.main()
