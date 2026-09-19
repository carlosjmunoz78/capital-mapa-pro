import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.evaluate_digital_twin_scenario import evaluate

class TwinScenarioTests(unittest.TestCase):
    def _snap(self):
        return {
            "company_id":"fenix","engine_id":"TWIN-001","environment":"LAB","version":"1.0.0",
            "snapshot_id":"twin-1","external_mutation_allowed":False,"writes_to_prod":False
        }

    def test_capacity_cost_scenario_is_simulated_only(self):
        out=evaluate(self._snap(),{
            "company_id":"fenix","scenario_id":"s1",
            "baseline_metrics":{"capacity_units":100,"cost_eur":50,"sla_minutes":60,"error_rate":0.02},
            "changes":[
                {"metric":"capacity_units","operation":"MULTIPLY","value":1.2},
                {"metric":"cost_eur","operation":"ADD","value":5}
            ]
        })
        self.assertEqual(out["after"]["capacity_units"],120)
        self.assertEqual(out["after"]["cost_eur"],55)
        self.assertIn("COST_INCREASE",out["adverse_signals"])
        self.assertEqual(out["status"],"REVIEW")
        self.assertFalse(out["promotion_allowed"])
        self.assertFalse(out["external_mutation_allowed"])
        self.assertFalse(out["writes_to_prod"])
        self.assertFalse(out["live_traffic_exposed"])

    def test_improvement_can_be_green_but_never_promoted(self):
        out=evaluate(self._snap(),{
            "company_id":"fenix","scenario_id":"s2",
            "baseline_metrics":{"sla_minutes":60,"error_rate":0.03},
            "changes":[
                {"metric":"sla_minutes","operation":"SET","value":45},
                {"metric":"error_rate","operation":"SET","value":0.01}
            ]
        })
        self.assertEqual(out["status"],"GREEN")
        self.assertFalse(out["promotion_allowed"])
        self.assertFalse(out["production_ready"])

    def test_cross_company_denied(self):
        with self.assertRaisesRegex(ValueError,"cross-company"):
            evaluate(self._snap(),{
                "company_id":"aion","scenario_id":"x","baseline_metrics":{"cost_eur":1},"changes":[]
            })

    def test_prod_snapshot_denied(self):
        snap=self._snap(); snap["environment"]="PROD"
        with self.assertRaisesRegex(ValueError,"cannot target PROD"):
            evaluate(snap,{"company_id":"fenix","scenario_id":"x","baseline_metrics":{"cost_eur":1},"changes":[]})

if __name__=="__main__": unittest.main()
