import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "app_gateway_authenticated_e2e_plan.py"
spec = importlib.util.spec_from_file_location("app_gateway_authenticated_e2e_plan", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AuthenticatedGatewayE2EPlanTests(unittest.TestCase):
    def test_live_target_boundary_is_five_routes(self):
        result = module.assess()
        self.assertEqual(result["target_count"], 5)
        self.assertEqual(result["read_only_targets"], ("notifications_list",))
        self.assertEqual(
            set(result["write_targets"]),
            {"notification_mark", "contact_create", "exp_create", "sign_create"},
        )

    def test_cleanup_strategies_are_proven_for_all_write_targets(self):
        result = module.assess()
        self.assertEqual(result["write_targets_without_proven_cleanup_strategy"], ())
        self.assertEqual(result["write_targets_without_proven_cleanup_route"], ())
        for name in result["write_targets"]:
            self.assertTrue(module.TARGETS[name]["cleanup_strategy_proven"])
            self.assertTrue(module.TARGETS[name]["cleanup_strategy"])

    def test_write_e2e_still_fails_closed_without_high_risk_gate(self):
        result = module.assess(safe_test_identity_proven=True)
        self.assertFalse(result["write_execution_allowed"])
        self.assertEqual(result["human_required"], "HIGH_RISK")
        self.assertEqual(result["status"], "BLOCKED_FAIL_CLOSED")

    def test_identity_plus_explicit_high_risk_gate_makes_plan_ready(self):
        result = module.assess(safe_test_identity_proven=True, high_risk_approved=True)
        self.assertTrue(result["write_execution_allowed"])
        self.assertIsNone(result["human_required"])
        self.assertEqual(result["status"], "READY_FOR_CONTROLLED_EXECUTION")

    def test_server_rpc_contracts_match_live_gateway_v17(self):
        self.assertEqual(module.TARGETS["notifications_list"]["server_rpc"], "fenix_prod_notifications_list_server")
        self.assertEqual(module.TARGETS["notification_mark"]["server_rpc"], "fenix_prod_notification_mark_server")
        self.assertEqual(module.TARGETS["contact_create"]["server_rpc"], "fenix_prod_contact_create_server")
        self.assertEqual(module.TARGETS["exp_create"]["server_rpc"], "fenix_prod_exp_create_server")
        self.assertEqual(module.TARGETS["sign_create"]["server_rpc"], "fenix_prod_sign_create_server")


if __name__ == "__main__":
    unittest.main()
