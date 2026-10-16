import sys
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import verify

class S2Offline(unittest.TestCase):
    def test_reference_conservation_and_rush(self):
        s=verify.scenario()
        data=verify.independent_reference(s)
        self.assertEqual(len(data),41)
        result=verify.check_invariants(data,"BASELINE",s)
        self.assertTrue(result["all_pass"],result)
        self.assertEqual(data[0]["preparationRate"],0)
        self.assertEqual(data[0]["dispatchRate"],0)
        self.assertTrue(data[16]["unpreparedOrders"]>0)
        self.assertAlmostEqual(sum(row["acceptedRate"]*.25 for row in data[:-1]),44,places=8)

    def test_independent_rates_stop_at_four(self):
        cfg=verify.scenario()
        self.assertEqual([verify.rate_at(x,cfg) for x in [0,1.75,2,3.75,4,10]],[6,6,16,16,0,0])

    def test_comparator_rejects_broken_series(self):
        cfg=verify.scenario()
        a=verify.independent_reference(cfg)
        b=[dict(x) for x in a]
        self.assertTrue(verify.pair(a,b,"IDENTICAL",1e-6)["pass"])
        b[20]["deliveredOrders"]+=.01
        self.assertFalse(verify.pair(a,b,"MODIFIED",1e-6)["pass"])

    def test_components_use_library_stocks_and_bounded_rates(self):
        r=verify.audit_component_reuse()
        self.assertEqual(r["preexisting_library_stock_components"],{"Level":2,"Level1a":1})
        self.assertEqual(r["preexisting_library_rate_components"],{"Rate_1":1,"RRate":2})
        self.assertEqual(r["connections_explicit"],5)
        self.assertEqual(r["differential_equations_authored_in_component_model"],0)
        self.assertEqual(r["differential_equations_authored_in_equation_model"],3)
        self.assertEqual(r["estimated_authoring_time_or_effort_saved"],"NOT_MEASURED")

    def test_s2_does_not_copy_s1_lookup_or_original_mdl(self):
        txt=(HERE/"IGCS2MakeToOrder.mo").read_text()
        self.assertNotIn("CapUtil",txt)
        self.assertNotIn("Hines",txt)
        self.assertFalse(list(HERE.glob("*.mdl")))
        for key in ["SystemDynamics.Rates.RRate","connect(prepare.y1,awaitingWork.u2)","connect(dispatch.y,deliveredLevel.u1)"]:
            self.assertIn(key,txt)

if __name__=="__main__":unittest.main()
