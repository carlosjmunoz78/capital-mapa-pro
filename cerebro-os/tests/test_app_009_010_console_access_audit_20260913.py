import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class App009010ConsoleAccessAuditTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_009_010_console_access_audit_20260913.py"))

    def test_profile_surface_exists_but_dead_cerebro_link_is_not_added(self):
        result = self.mod["assess"]()
        audit = self.mod["AUDIT"]["APP_009_carlos_access"]
        self.assertTrue(result["APP_009_profile_surface_green"])
        self.assertFalse(result["APP_009_cerebro_link_green"])
        self.assertFalse(result["safe_to_add_cerebro_profile_link_now"])
        self.assertEqual(audit["profile_route"], "/perfil")
        self.assertFalse(audit["cerebro_web_route_present"])

    def test_console_gateway_contract_is_green_but_not_yet_deployable(self):
        result = self.mod["assess"]()
        audit = self.mod["AUDIT"]["APP_010_cerebro_gateway"]
        self.assertTrue(result["APP_010_logical_gateway_green"])
        self.assertFalse(result["APP_010_deployable_surface_green"])
        self.assertEqual(audit["pipeline_path"], ("CONSOLE", "GATEWAY", "POLICY", "ENGINE", "AUDIT"))
        self.assertFalse(audit["direct_model_path_present"])
        self.assertEqual(audit["unknown_command_fail_closed"], ("HUMAN_REQUIRED", "LOW_CONFIDENCE"))


if __name__ == "__main__":
    unittest.main()
