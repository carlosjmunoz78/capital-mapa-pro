import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "identity" / "read_only_browser_allowlist_v0.py"
spec = importlib.util.spec_from_file_location("browser_allowlist", SOURCE)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class PublicMetadataAllowlistTests(unittest.TestCase):
    def policy(self, **overrides):
        args = dict(company_id="fenix", environment="LAB", version="v0",
                    allowed_origins=("https://example.com/",),
                    connector_available=False, user_approved_origins=True,
                    bridge_online=True, extension_fresh=True,
                    change_control_green=True)
        args.update(overrides)
        return module.AllowlistPolicy(**args)

    def test_existing_fixed_pilot_can_be_planned(self):
        plan = module.plan_public_metadata_navigation(self.policy(), "https://example.com/")
        self.assertEqual(plan["status"], "GREEN")
        self.assertEqual(plan["decision"], "ALLOW_EXISTING_FIXED_METADATA_PILOT")
        self.assertEqual(plan["redirect_policy"], "DENY")
        for key in ("page_content_access", "cookie_access", "form_interaction",
                    "external_mutation_allowed", "prod_activation_allowed"):
            self.assertFalse(plan[key])

    def test_new_origin_requires_runtime_upgrade_even_when_approved(self):
        policy = self.policy(allowed_origins=("https://example.com/", "https://example.org/"))
        plan = module.plan_public_metadata_navigation(policy, "https://example.org/")
        self.assertEqual(plan["status"], "BLOCKED")
        self.assertIn("RUNTIME_NOT_IMPLEMENTED_FOR_TARGET", plan["blockers"])
        self.assertIsNone(plan["target_url"])

    def test_connector_first_and_explicit_approval(self):
        plan = module.plan_public_metadata_navigation(
            self.policy(connector_available=True, user_approved_origins=False),
            "https://example.com/")
        self.assertEqual(plan["status"], "BLOCKED")
        self.assertIn("CONNECTOR_FIRST", plan["blockers"])
        self.assertIn("EXPLICIT_ORIGIN_APPROVAL_REQUIRED", plan["blockers"])

    def test_scope_and_live_policy_guards(self):
        plan = module.plan_public_metadata_navigation(
            self.policy(company_id="other", environment="PROD", version="v1",
                        bridge_online=False, extension_fresh=False,
                        change_control_green=False), "https://example.com/")
        self.assertEqual(plan["status"], "BLOCKED")
        self.assertIn("LAB_PILOT_SCOPE_REQUIRED", plan["blockers"])
        self.assertIn("LIVE_EXTENSION_REQUIRED", plan["blockers"])
        self.assertIn("CHANGE_CONTROL_REQUIRED", plan["blockers"])

    def test_rejects_noncanonical_suspicious_and_redirect_targets(self):
        invalid = (
            "http://example.com/", "https://example.com", "https://example.com/path",
            "https://example.com/?q=1", "https://example.com/#fragment",
            "https://example.com:443/", "https://u:p@example.com/",
            "https://example.com.evil/", "https://127.0.0.1/",
            "https://localhost/", "https://a..com/", "https://example.com./",
            "https://EXAMPLE.com/", "javascript:alert(1)", "//example.com/",
        )
        for url in invalid:
            with self.subTest(url=url):
                plan = module.plan_public_metadata_navigation(self.policy(), url)
                self.assertEqual(plan["status"], "BLOCKED")
                self.assertIn("ORIGIN_NOT_EXACTLY_ALLOWLISTED", plan["blockers"])

    def test_invalid_policy_origin_fails_closed(self):
        plan = module.plan_public_metadata_navigation(
            self.policy(allowed_origins=("https://example.com/", "http://untrusted.test/")),
            "https://example.com/")
        self.assertEqual(plan["status"], "BLOCKED")
        self.assertIn("ORIGIN_NOT_EXACTLY_ALLOWLISTED", plan["blockers"])


if __name__ == "__main__":
    unittest.main()
