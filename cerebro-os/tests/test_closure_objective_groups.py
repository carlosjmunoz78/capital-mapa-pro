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

    def test_security_tracks_live_rls_wrapper_parity_and_deployed_app_blocker(self):
        security = module.OBJECTIVE_GROUPS["SECURITY"]
        self.assertIn("44_of_44_fenix_prod_tables_rls_enabled_live", security["completed"])
        self.assertIn("five_target_server_wrappers_live_security_definer_service_role_only", security["completed"])
        self.assertIn("five_target_server_wrappers_unknown_actor_fail_closed", security["completed"])
        self.assertIn("exp_create_and_sign_create_null_actor_guard_hardened_live", security["completed"])
        self.assertIn("five_target_old_new_rpc_parity_green_in_rolled_back_prod_transaction", security["completed"])
        self.assertIn("app_gateway_v17_required_target_routes_live", security["completed"])
        self.assertIn("app_branch_persisted_direct_prod_rpc_callers_zero_ci_34786441006", security["completed"])
        self.assertIn("live_deploy_channel_identified_as_github_pages_gh_pages", security["completed"])
        self.assertIn("live_deployed_source_sha_c7a15cff9a387f1f142c8eeb06fd83a799e85a61", security["completed"])
        self.assertIn("live_deployed_contact_direct_rpc_fenix_prod_contact_create_v2_confirmed", security["completed"])
        self.assertIn("deploy_or_promote_reviewed_rpc_migration_without_bypassing_human_prod_gate", security["remaining"])
        self.assertIn("live_deployed_app_direct_caller_zero_evidence_after_promotion", security["remaining"])
        self.assertIn("authenticated_http_gateway_e2e_for_target_routes", security["remaining"])
        self.assertIn("rollback_evidence_for_full_http_write_path", security["remaining"])
        self.assertIn("caller_retirement_evidence_before_any_legacy_privilege_change", security["remaining"])

    def test_observability_tracks_linkedin_green_and_youtube_reauth_without_false_retained_metric(self):
        observability = module.OBJECTIVE_GROUPS["OBSERVABILITY"]
        self.assertIn("linkedin_retained_health_execution_green", observability["completed"])
        self.assertIn("youtube_health_reauthorization_green", observability["completed"])
        self.assertIn("youtube_health_connection_rewired_green", observability["completed"])
        self.assertIn("youtube_retained_metric_execution_or_explicit_approved_absence_policy", observability["remaining"])


if __name__ == "__main__":
    unittest.main()
