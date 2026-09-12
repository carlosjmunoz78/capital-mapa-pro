import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "identity"))

from connector_registry import ConnectorCapability, ConnectorRegistry
from computer_use_policy import ComputerUseRequest, evaluate_computer_use


class IdentityConnectorAndComputerUsePolicyTests(unittest.TestCase):
    def test_connector_priority_prefers_official_then_existing_then_mcp(self):
        registry = ConnectorRegistry()
        registry.register(ConnectorCapability("browser", "fenix", "publish", "COMPUTER_USE", "LAB"))
        registry.register(ConnectorCapability("mcp", "fenix", "publish", "MCP", "LAB"))
        registry.register(ConnectorCapability("existing", "fenix", "publish", "EXISTING_CONNECTOR", "LAB"))
        registry.register(ConnectorCapability("api", "fenix", "publish", "OFFICIAL_API", "LAB"))
        self.assertEqual(registry.route("fenix", "publish", "LAB").connector_id, "api")

    def test_computer_use_allowed_only_as_fallback(self):
        out = evaluate_computer_use(
            ComputerUseRequest(
                company_id="fenix",
                engine_id="ACCOUNT-LIFECYCLE",
                environment="LAB",
                version="1.0.0",
                capability="create_social_account",
                action="CREATE_ACCOUNT",
                higher_priority_connector_available=False,
                account_registered=True,
                credential_reference_available=True,
                policy_green=True,
                confidence=0.95,
            )
        )
        self.assertTrue(out["computer_use_allowed"])
        self.assertTrue(out["kill_switch_required"])
        self.assertTrue(out["audit_log_required"])
        self.assertFalse(out["credential_value_exposure_allowed"])
        self.assertFalse(out["secret_copy_to_prompt_allowed"])

    def test_higher_priority_connector_blocks_browser_fallback(self):
        out = evaluate_computer_use(
            ComputerUseRequest(
                company_id="fenix",
                engine_id="ACCOUNT-LIFECYCLE",
                environment="LAB",
                version="1.0.0",
                capability="publish",
                action="PUBLISH_DRAFT",
                higher_priority_connector_available=True,
                account_registered=True,
                credential_reference_available=True,
                policy_green=True,
                confidence=0.99,
            )
        )
        self.assertFalse(out["computer_use_allowed"])
        self.assertIn("USE_HIGHER_PRIORITY_CONNECTOR", out["blockers"])

    def test_signature_and_money_limit_require_human(self):
        signature = evaluate_computer_use(
            ComputerUseRequest(
                company_id="fenix",
                engine_id="ACCOUNT-LIFECYCLE",
                environment="PROD",
                version="1.0.0",
                capability="legal",
                action="BINDING_SIGNATURE",
                higher_priority_connector_available=False,
                account_registered=True,
                credential_reference_available=True,
                policy_green=True,
                confidence=0.99,
            )
        )
        self.assertTrue(signature["human_required"])
        self.assertEqual(signature["human_reason"], "SIGNATURE_REQUIRED")
        self.assertFalse(signature["computer_use_allowed"])

        money = evaluate_computer_use(
            ComputerUseRequest(
                company_id="fenix",
                engine_id="ADS",
                environment="PROD",
                version="1.0.0",
                capability="ads",
                action="CREATE_CAMPAIGN",
                higher_priority_connector_available=False,
                account_registered=True,
                credential_reference_available=True,
                policy_green=True,
                confidence=0.99,
                money_amount=101,
                money_limit=100,
            )
        )
        self.assertTrue(money["human_required"])
        self.assertEqual(money["human_reason"], "MONEY_LIMIT")
        self.assertFalse(money["computer_use_allowed"])


if __name__ == "__main__":
    unittest.main()
