import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ConsoleDeployReadinessTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_009_010_console_deploy_readiness_20260914.py"))

    def test_http_and_web_contracts_are_green_without_overstating_deployment(self):
        result = self.mod["assess"]()
        self.assertTrue(result["APP_010_http_contract_green"])
        self.assertTrue(result["APP_010_web_ui_green"])
        self.assertFalse(result["APP_010_deployable_green"])
        self.assertEqual(result["status"], "HTTP_AND_WEB_UI_GREEN_DEPLOYED_URL_OPEN")

    def test_profile_link_and_prod_promotion_fail_closed_until_real_url_exists(self):
        result = self.mod["assess"]()
        self.assertFalse(result["APP_009_profile_link_ready"])
        self.assertFalse(result["production_promotion_allowed"])


if __name__ == "__main__":
    unittest.main()
