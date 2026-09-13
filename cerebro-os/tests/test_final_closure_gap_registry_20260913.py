import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FinalClosureGapRegistryTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "final_closure_gap_registry.py"))

    def test_exact_five_global_blockers_remain_fail_closed(self):
        result = self.mod["assess_final_closure_gaps"]()
        self.assertEqual(result["gap_count"], 5)
        self.assertEqual(result["blocking_count"], 5)
        self.assertFalse(result["perfect"])
        self.assertFalse(result["prod_candidate_allowed"])
        self.assertFalse(result["prod_green"])
        self.assertFalse(result["automatic_prod_promotion_allowed"])
        self.assertEqual(result["status"], "FIVE_GLOBAL_GAPS_REMAIN")

    def test_finops_is_classified_under_finops_and_never_estimated(self):
        gaps = self.mod["GAPS"]
        self.assertIn("FINOPS:monthly_cost_measured", gaps)
        self.assertNotIn("OBSERVABILITY:monthly_cost_measured", gaps)
        self.assertFalse(gaps["FINOPS:monthly_cost_measured"]["estimated_amounts_used"])

    def test_youtube_reauth_does_not_fake_retained_metric_green(self):
        row = self.mod["GAPS"]["OBSERVABILITY:per_engine_logs_metrics_incidents_complete"]
        self.assertTrue(row["youtube_reauthorized_and_rewired_green"])
        self.assertFalse(row["youtube_retained_metric_green"])

    def test_rls_human_gate_is_approved_but_prod_change_stays_blocked(self):
        row = self.mod["GAPS"]["SECURITY:supabase_security_review_green"]
        self.assertEqual(row["human_gate_for_four_table_rls"], "APPROVED")
        self.assertFalse(row["automatic_prod_change_allowed"])
        self.assertTrue(row["blocking"])


if __name__ == "__main__":
    unittest.main()
