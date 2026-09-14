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

    def test_write_e2e_is_fail_closed_without_identity_and_cleanup(self):
        result = module.assess()
        self.assertFalse(result["write_execution_allowed"])
        self.assertEqual(result["human_required"], "HIGH_RISK")
        self.assertEqual(result["status"], "BLOCKED_FAIL_CLOSED")
        self.assertEqual(
            set(result["write_targets_without_proven_cleanup_route"]),
            {"notification_mark", "contact_create", "exp_create", "sign_create"},
        )

    def test_high_risk_approval_alone_cannot_bypass_cleanup_contract(self):
        result = module.assess(safe_test_identity_proven=True, high_risk_approved=True)
        self.assertFalse(result["write_execution_allowed"])
        self.assertEqual(result["status"], "BLOCKED_FAIL_CLOSED")

    def test_server_rpc_contracts_match_live_gateway_v17(self):
        self.assertEqual(module.TARGETS["notifications_list"]["server_rpc"], "fenix_prod_notifications_list_server")
        self.assertEqual(module.TARGETS["notification_mark"]["server_rpc"], "fenix_prod_notification_mark_server")
        self.assertEqual(module.TARGETS["contact_create"]["server_rpc"], "fenix_prod_contact_create_server")
        self.assertEqual(module.TARGETS["exp_create"]["server_rpc"], "fenix_prod_exp_create_server")
        self.assertEqual(module.TARGETS["sign_create"]["server_rpc"], "fenix_prod_sign_create_server")


if __name__ == "__main__":
    unittest.main()
