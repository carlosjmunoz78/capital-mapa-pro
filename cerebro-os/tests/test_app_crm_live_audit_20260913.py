import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AppCrmLiveAuditTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_crm_live_audit_20260913.py"))

    def test_app_and_crm_read_only_baseline_are_green(self):
        result = self.mod["assess"]()
        self.assertTrue(result["APP_001_read_only_inventory_green"])
        self.assertTrue(result["CRM_001_live_inventory_green"])
        self.assertTrue(result["app_repo_unchanged"])
        self.assertTrue(result["app_preprod_stays_cancelled"])
        self.assertTrue(result["ready_for_next_read_only_audit"])

    def test_security_retirement_stays_fail_closed_while_direct_caller_exists(self):
        result = self.mod["assess"]()
        audit = self.mod["AUDIT"]
        self.assertTrue(result["security_rpc_retirement_blocked"])
        self.assertTrue(audit["security_caller_evidence"]["direct_prod_rpc_callers_still_exist"])
        self.assertFalse(audit["security_caller_evidence"]["safe_to_revoke_authenticated_execute_now"])

    def test_gateway_custom_auth_is_recorded_without_claiming_edge_flag_jwt(self):
        gateway = self.mod["AUDIT"]["prod_gateway"]
        self.assertFalse(gateway["edge_verify_jwt_flag"])
        self.assertTrue(gateway["custom_bearer_validation_present"])
        self.assertTrue(gateway["custom_identity_uses_auth_get_user"])
        self.assertTrue(gateway["actor_context_resolution_present"])


if __name__ == "__main__":
    unittest.main()
