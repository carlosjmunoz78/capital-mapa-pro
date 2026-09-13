import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ConsoleDeployReadinessTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_009_010_console_deploy_readiness_20260914.py"))

    def test_http_web_and_branch_launcher_are_green_without_overstating_deployment(self):
        result = self.mod["assess"]()
        self.assertTrue(result["APP_010_http_contract_green"])
        self.assertTrue(result["APP_010_web_ui_green"])
        self.assertTrue(result["APP_009_profile_launcher_branch_green"])
        self.assertFalse(result["APP_010_deployable_green"])
        self.assertEqual(result["status"], "PROFILE_LAUNCHER_BRANCH_GREEN_DEPLOYED_URL_OPEN")

    def test_profile_link_and_prod_promotion_fail_closed_until_real_url_exists(self):
        result = self.mod["assess"]()
        self.assertFalse(result["APP_009_profile_link_ready"])
        self.assertFalse(result["production_promotion_allowed"])
        self.assertEqual(
            result["safe_next"],
            "deploy_authenticated_console_gateway_url_then_prove_live_profile_launcher_and_enable_prod_promotion_gate",
        )


if __name__ == "__main__":
    unittest.main()
