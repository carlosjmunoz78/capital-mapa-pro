import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "identity"))

from connector_registry import ConnectorCapability, ConnectorRegistry
from computer_use_policy import ComputerUseRequest, evaluate_computer_use
from account_registry import IdentityRecord, AccountRecord, IdentityAccountRegistry
from credential_scope import ScopedCredentialRef, authorize_credential_ref
from account_lifecycle import AccountLifecycleRequest, plan_account_lifecycle


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

    def test_identity_account_registry_enforces_company_environment_version_scope(self):
        registry=IdentityAccountRegistry()
        registry.register_identity(IdentityRecord("id-fenix","COMPANY","fenix","fenix","Fenix","default","LAB","1.0.0"))
        registry.register_account(AccountRecord("acct-1","id-fenix","fenix","google","ops@fenix.example","OAUTH","operations","LAB","1.0.0"))
        self.assertEqual(registry.account("fenix","acct-1","LAB","1.0.0").provider,"google")
        with self.assertRaisesRegex(ValueError,"cross-company"):
            registry.register_account(AccountRecord("acct-2","id-fenix","aion","google","ops@aion.example","OAUTH","operations","LAB","1.0.0"))

    def test_scoped_credential_reference_never_exposes_value_and_denies_scope_mismatch(self):
        ref=ScopedCredentialRef(
            credential_ref_id="cred-1",account_id="acct-1",identity_id="id-fenix",company_id="fenix",
            vault_provider="GITHUB_SECRETS",secret_ref="FENIX_GOOGLE_OAUTH",environment="LAB",version="1.0.0",scopes=("read",)
        )
        out=authorize_credential_ref(
            credential=ref,company_id="fenix",identity_id="id-fenix",account_id="acct-1",environment="LAB",version="1.0.0"
        )
        self.assertTrue(out["authorized"])
        self.assertFalse(out["secret_value_exposed"])
        with self.assertRaisesRegex(PermissionError,"scope mismatch"):
            authorize_credential_ref(
                credential=ref,company_id="aion",identity_id="id-fenix",account_id="acct-1",environment="LAB",version="1.0.0"
            )

    def test_account_lifecycle_reuses_existing_before_creating(self):
        out=plan_account_lifecycle(AccountLifecycleRequest(
            company_id="fenix",identity_id="id-fenix",provider="linkedin",purpose="marketing",
            environment="LAB",version="1.0.0",existing_reusable_account=True,policy_green=True
        ))
        self.assertEqual(out["decision"],"REUSE_EXISTING_ACCOUNT")
        self.assertFalse(out["create_account_allowed"])

    def test_account_lifecycle_human_only_step_and_prod_are_fail_closed(self):
        human=plan_account_lifecycle(AccountLifecycleRequest(
            company_id="fenix",identity_id="id-fenix",provider="provider",purpose="operations",
            environment="PREPROD",version="1.0.0",existing_reusable_account=False,policy_green=True,
            required_human_steps=("HUMAN_MFA",)
        ))
        self.assertEqual(human["status"],"HUMAN_REQUIRED")
        self.assertEqual(human["human_reason"],"HIGH_RISK")
        prod=plan_account_lifecycle(AccountLifecycleRequest(
            company_id="fenix",identity_id="id-fenix",provider="provider",purpose="operations",
            environment="PROD",version="1.0.0",existing_reusable_account=False,policy_green=True
        ))
        self.assertEqual(prod["status"],"GREEN")
        self.assertFalse(prod["create_account_allowed"])
        self.assertFalse(prod["production_creation_allowed"])

    def test_raw_secret_text_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"embedded secret"):
            ScopedCredentialRef(
                credential_ref_id="cred-x",account_id="acct",identity_id="id",company_id="fenix",
                vault_provider="VAULT_REF",secret_ref="token=plaintext",environment="LAB"
            ).validate()


if __name__ == "__main__":
    unittest.main()
