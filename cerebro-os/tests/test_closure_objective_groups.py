import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "closure_objective_groups.py"
spec = importlib.util.spec_from_file_location("closure_objective_groups", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ClosureObjectiveGroupsTests(unittest.TestCase):
    def test_execution_order_and_fail_closed_status(self):
        result = module.assess_objective_groups()
        self.assertEqual(
            result["execution_order"],
            ("SECURITY", "RECOVERY", "OBSERVABILITY", "FINOPS", "PROMOTION"),
        )
        self.assertFalse(result["all_green"])
        self.assertFalse(result["prod_candidate_allowed"])
        self.assertFalse(result["automatic_prod_promotion_allowed"])
        self.assertEqual(result["status"], "GREEN_LOOP_IN_PROGRESS")

    def test_all_groups_have_remaining_evidence_until_proven(self):
        result = module.assess_objective_groups()
        self.assertEqual(set(result["pending_groups"]), set(result["execution_order"]))
        for name in result["execution_order"]:
            row = result["groups"][name]
            self.assertFalse(row["green"])
            self.assertTrue(row["remaining"])

    def test_security_tracks_current_caller_and_rls_evidence_fail_closed(self):
        security = module.OBJECTIVE_GROUPS["SECURITY"]
        self.assertIn("6_current_frontend_direct_callers_verified_at_app_head", security["completed"])
        self.assertIn("9_remaining_mutators_frontend_negative_search_recorded_fail_closed", security["completed"])
        self.assertIn("9_remaining_mutators_expanded_repo_negative_search_recorded_fail_closed", security["completed"])
        self.assertIn("four_table_rls_isolated_lab_green", security["completed"])
        self.assertIn("four_table_rls_high_risk_human_gate_approved", security["completed"])
        self.assertIn("global_caller_absence_or_retirement_evidence_not_yet_proven", security["remaining"])
        self.assertIn("apply_approved_four_table_rls_change_in_prod_when_execution_channel_allows", security["remaining"])

    def test_observability_tracks_linkedin_green_and_youtube_reauth_without_false_retained_metric(self):
        observability = module.OBJECTIVE_GROUPS["OBSERVABILITY"]
        self.assertIn("linkedin_retained_health_execution_green", observability["completed"])
        self.assertIn("youtube_health_reauthorization_green", observability["completed"])
        self.assertIn("youtube_health_connection_rewired_green", observability["completed"])
        self.assertIn("youtube_retained_metric_execution_or_explicit_approved_absence_policy", observability["remaining"])


if __name__ == "__main__":
    unittest.main()
