import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AppCrmModuleAuditTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_crm_module_audit_20260913.py"))

    def test_read_only_modules_are_evidenced_without_mutating_app(self):
        result = self.mod["assess"]()
        self.assertTrue(result["APP_003_green"])
        self.assertTrue(result["APP_004_audit_green"])
        self.assertTrue(result["APP_005_green"])
        self.assertTrue(result["APP_006_audit_green"])
        self.assertTrue(result["app_main_unchanged"])
        self.assertTrue(result["app_preprod_stays_cancelled"])

    def test_communications_stays_fail_closed_on_prod_wiring_mismatch(self):
        result = self.mod["assess"]()
        audit = self.mod["AUDIT"]["APP_007_communications"]
        self.assertFalse(result["APP_007_green"])
        self.assertTrue(audit["prod_edge_active"])
        self.assertEqual(audit["prod_edge_slug"], "fenix-communications-gateway")
        self.assertEqual(audit["shell_calls_test_slug"], "fenix-communications-gateway-test")
        self.assertFalse(audit["automatic_real_send_claimed"])

    def test_signature_and_notification_gateway_gaps_remain_explicit(self):
        audit = self.mod["AUDIT"]
        self.assertTrue(audit["APP_004_tasks_notifications"]["notification_server_wrappers_missing"])
        self.assertTrue(audit["APP_006_signatures"]["create_server_wrapper_missing"])
        self.assertTrue(audit["APP_006_signatures"]["signature_human_gate_preserved"])


if __name__ == "__main__":
    unittest.main()
