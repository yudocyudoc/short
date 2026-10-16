"""Fast, offline invariants. These do NOT establish OpenModelica parity."""
import csv,json,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
from compare import compare,read_csv,FIELDS

class TestParityContract(unittest.TestCase):
    def test_s1_conditions_match_pysd_fixture(self):
        cfg=json.loads((ROOT/"experiments/molecule-composer-v1/synthetic_mts.json").read_text())
        self.assertEqual((cfg["dt_hours"],cfg["duration_hours"]),(.25,8))
        self.assertEqual((cfg["capacity_orders_per_hour"],cfg["planned_production_orders_per_hour"],cfg["accepted_orders_per_hour"]),(12,8,6))
        self.assertEqual((cfg["initial_accepted_unshipped_orders"],cfg["initial_finished_goods_orders"]),(5,12))
    def test_lookup_coordinates_preserved(self):
        source=json.loads((ROOT/"experiments/hines-pysd/specifications_extracted.json").read_text())["models"]
        model=(HERE/"IGCS1Parity.mo").read_text()
        for modelname,xkey,ykey in (("CapUtil.mdl","capX","capY"),("invbakf.mdl","shipX","shipY")):
            coordinates=source[modelname]["lookup"]
            for axis,var in ((0,xkey),(1,ykey)):
                points=",".join(str(row[axis]) for row in coordinates)
                self.assertIn(var,model)
                self.assertIn("{"+points+"}",model)
    def test_solver_and_steps(self):
        for f in ("equations.mos","components.mos"):
            txt=(HERE/f).read_text()
            self.assertIn('method="euler"',txt)
            self.assertIn("numberOfIntervals=32",txt)
    def test_comparator_accepts_identical_and_rejects_different(self):
        py=[];other=[]
        for n in range(33):
            py.append({"time_hours":str(n*.25),
               "model_backlog_orders":"5","model_finished_stock_orders":"12",
               "model_production_per_hour":"8","model_shipping_per_hour":"6"})
            other.append({"time":str(n*.25),
               "backlog":"5","inventory":"12","production":"8","shipping":"6"})
        self.assertTrue(compare(py,other,"TEST",1e-6)["all_points_within_tolerance"])
        other[20]["shipping"]="7"
        self.assertFalse(compare(py,other,"TEST",1e-6)["all_points_within_tolerance"])
    def test_no_original_hines_mdl_in_git_tree(self):
        self.assertFalse(list(HERE.rglob("*.mdl")))
        self.assertFalse(list(HERE.rglob("*.mdl.bin")))

if __name__=="__main__":unittest.main()
