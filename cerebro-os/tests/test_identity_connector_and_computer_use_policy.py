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
from access_orchestrator import AccessExecutionRequest, plan_access_execution
from session_discovery import SessionObservation, discover_session_metadata
from connector_gap_planner import ConnectorGapRequest, plan_connector_gap
from multiaccount_session_registry import SessionBinding, MultiAccountSessionRegistry
from session_renewal import SessionRenewalRequest, plan_session_renewal
from execution_guard import ExecutionGuardRequest, evaluate_execution_guard


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

    def _access_fixture(self):
        registry=IdentityAccountRegistry()
        registry.register_identity(IdentityRecord("id-fenix","COMPANY","fenix","fenix","Fenix","default","LAB","1.0.0"))
        registry.register_account(AccountRecord("acct-1","id-fenix","fenix","linkedin","ops@fenix.example","OAUTH","marketing","LAB","1.0.0"))
        credential=ScopedCredentialRef(
            credential_ref_id="cred-1",account_id="acct-1",identity_id="id-fenix",company_id="fenix",
            vault_provider="GITHUB_SECRETS",secret_ref="FENIX_LINKEDIN_OAUTH",environment="LAB",version="1.0.0"
        )
        return registry,credential

    def test_access_orchestrator_prefers_higher_priority_connector(self):
        registry,credential=self._access_fixture()
        connectors=ConnectorRegistry()
        connectors.register(ConnectorCapability("api","fenix","publish","OFFICIAL_API","LAB"))
        connectors.register(ConnectorCapability("browser","fenix","publish","COMPUTER_USE","LAB"))
        out=plan_access_execution(
            AccessExecutionRequest("fenix","id-fenix","acct-1","SOC-001","publish","PUBLISH_DRAFT","LAB","1.0.0"),
            registry=registry,credential=credential,connectors=connectors
        )
        self.assertEqual(out["decision"],"USE_HIGHER_PRIORITY_CONNECTOR")
        self.assertEqual(out["connector_id"],"api")
        self.assertFalse(out["computer_use_allowed"])
        self.assertFalse(out["secret_value_exposed"])

    def test_access_orchestrator_allows_computer_use_only_as_scoped_fallback(self):
        registry,credential=self._access_fixture()
        connectors=ConnectorRegistry()
        connectors.register(ConnectorCapability("browser","fenix","publish","COMPUTER_USE","LAB"))
        out=plan_access_execution(
            AccessExecutionRequest("fenix","id-fenix","acct-1","SOC-001","publish","PUBLISH_DRAFT","LAB","1.0.0",True,0.95),
            registry=registry,credential=credential,connectors=connectors
        )
        self.assertEqual(out["status"],"GREEN")
        self.assertEqual(out["decision"],"COMPUTER_USE_FALLBACK")
        self.assertTrue(out["computer_use_allowed"])
        self.assertFalse(out["secret_value_exposed"])

    def test_access_orchestrator_blocks_browser_when_credential_reference_missing(self):
        registry,_=self._access_fixture()
        connectors=ConnectorRegistry()
        connectors.register(ConnectorCapability("browser","fenix","publish","COMPUTER_USE","LAB"))
        out=plan_access_execution(
            AccessExecutionRequest("fenix","id-fenix","acct-1","SOC-001","publish","PUBLISH_DRAFT","LAB","1.0.0",True,0.95),
            registry=registry,credential=None,connectors=connectors
        )
        self.assertEqual(out["status"],"BLOCKED")
        self.assertIn("CREDENTIAL_REFERENCE_MISSING",out["blockers"])
        self.assertFalse(out["computer_use_allowed"])

    def test_access_orchestrator_denies_identity_account_mismatch(self):
        registry,credential=self._access_fixture()
        connectors=ConnectorRegistry()
        with self.assertRaisesRegex(PermissionError,"identity/account mismatch"):
            plan_access_execution(
                AccessExecutionRequest("fenix","other-id","acct-1","SOC-001","publish","PUBLISH_DRAFT","LAB","1.0.0"),
                registry=registry,credential=credential,connectors=connectors
            )

    def test_session_discovery_records_authenticated_state_without_extracting_secrets(self):
        out=discover_session_metadata(SessionObservation(
            company_id="fenix",provider="chrome-profile",environment="LAB",version="1.0.0",
            authenticated=True,login_method="SESSION",account_hint="marketing",
            profile_id="chrome-1",browser_family="CHROME",device_id="desktop-1",evidence_ref="e://session"
        ))
        self.assertEqual(out["status"],"AUTHENTICATED_SESSION_DISCOVERED")
        self.assertTrue(out["authenticated"])
        self.assertFalse(out["secret_value_exposed"])
        self.assertFalse(out["secret_extraction_allowed"])
        self.assertTrue(out["credential_reference_required_for_execution"])

    def test_session_discovery_never_attempts_password_recovery_just_because_login_is_missing(self):
        out=discover_session_metadata(SessionObservation(
            company_id="fenix",provider="linkedin",environment="LAB",version="1.0.0",
            authenticated=False,login_method="OAUTH"
        ))
        self.assertEqual(out["status"],"LOGIN_REQUIRED")
        self.assertFalse(out["password_recovery_attempted"])
        self.assertFalse(out["external_mutation_allowed"])

    def test_session_discovery_rejects_observed_secret_values(self):
        with self.assertRaisesRegex(ValueError,"secret extraction"):
            discover_session_metadata(SessionObservation(
                company_id="fenix",provider="provider",environment="LAB",version="1.0.0",
                authenticated=True,login_method="SESSION",secret_value_observed=True
            ))

    def test_connector_gap_reuses_existing_connector_before_factory(self):
        connectors=ConnectorRegistry()
        connectors.register(ConnectorCapability("api","fenix","publish","OFFICIAL_API","LAB"))
        out=plan_connector_gap(
            ConnectorGapRequest(company_id="fenix",capability="publish",environment="LAB"),
            connectors
        )
        self.assertEqual(out["decision"],"REUSE_EXISTING_CONNECTOR")
        self.assertIsNone(out["factory_request"])

    def test_connector_gap_prefers_official_api_when_known(self):
        connectors=ConnectorRegistry()
        out=plan_connector_gap(
            ConnectorGapRequest(company_id="fenix",capability="research",environment="LAB",official_api_known=True),
            connectors
        )
        self.assertEqual(out["decision"],"INTEGRATE_OFFICIAL_API")
        self.assertEqual(out["factory_request"]["preferred_type"],"OFFICIAL_API")
        self.assertIn("rollback",out["factory_request"]["requirements"])

    def test_connector_gap_builds_zero_cost_candidate_only_after_reuse_paths_fail(self):
        connectors=ConnectorRegistry()
        out=plan_connector_gap(
            ConnectorGapRequest(company_id="fenix",capability="custom_sync",environment="LAB"),
            connectors
        )
        self.assertEqual(out["decision"],"FACTORY_BUILD_CONNECTOR_CANDIDATE")
        self.assertEqual(out["connector_type"],"BUILT_CONNECTOR")
        self.assertFalse(out["factory_request"]["external_mutation_allowed"])
        self.assertFalse(out["factory_request"]["prod_activation_allowed"])
        self.assertIn("secret_refs_only",out["factory_request"]["requirements"])

    def test_connector_gap_never_auto_approves_paid_or_policy_risky_path(self):
        connectors=ConnectorRegistry()
        paid=plan_connector_gap(
            ConnectorGapRequest(company_id="fenix",capability="paid_api",environment="LAB",estimated_cost_eur=10),
            connectors
        )
        self.assertEqual(paid["status"],"HUMAN_REQUIRED")
        self.assertEqual(paid["human_reason"],"MONEY_LIMIT")
        risky=plan_connector_gap(
            ConnectorGapRequest(company_id="fenix",capability="restricted",environment="LAB",legal_or_terms_risk=True),
            connectors
        )
        self.assertEqual(risky["human_reason"],"POLICY_CONFLICT")

    def test_multiaccount_session_registry_isolates_accounts_and_scopes(self):
        registry=MultiAccountSessionRegistry()
        registry.register(SessionBinding(
            "sess-1","fenix","id-fenix","acct-1","linkedin","chrome-1","desktop-1","CHROME","LAB","1.0.0",True,"e://1"
        ))
        registry.register(SessionBinding(
            "sess-2","fenix","id-fenix","acct-2","google","chrome-2","desktop-1","CHROME","LAB","1.0.0",True,"e://2"
        ))
        self.assertEqual(registry.resolve_authenticated("fenix","acct-1","LAB","1.0.0").session_id,"sess-1")
        self.assertEqual(registry.resolve_authenticated("fenix","acct-2","LAB","1.0.0").session_id,"sess-2")
        with self.assertRaisesRegex(PermissionError,"session scope mismatch"):
            registry.assert_scope(
                registry.resolve_authenticated("fenix","acct-1","LAB","1.0.0"),
                company_id="aion",identity_id="id-fenix",account_id="acct-1",environment="LAB",version="1.0.0"
            )

    def test_session_renewal_keeps_existing_session_before_any_login(self):
        out=plan_session_renewal(SessionRenewalRequest(
            company_id="fenix",identity_id="id-fenix",account_id="acct-1",provider="linkedin",
            environment="LAB",version="1.0.0",authenticated=True,
            renewable_without_secret_exposure=True,higher_priority_connector_available=False,
            policy_green=True,confidence=0.99
        ))
        self.assertEqual(out["decision"],"KEEP_EXISTING_AUTHENTICATED_SESSION")
        self.assertFalse(out["browser_login_allowed"])
        self.assertFalse(out["secret_value_exposure_allowed"])

    def test_session_renewal_fails_closed_for_human_mfa_and_prod(self):
        human=plan_session_renewal(SessionRenewalRequest(
            company_id="fenix",identity_id="id-fenix",account_id="acct-1",provider="linkedin",
            environment="PREPROD",version="1.0.0",authenticated=False,
            renewable_without_secret_exposure=True,higher_priority_connector_available=False,
            policy_green=True,confidence=0.99,requires_human_mfa=True
        ))
        self.assertEqual(human["status"],"HUMAN_REQUIRED")
        self.assertEqual(human["human_reason"],"HIGH_RISK")
        prod=plan_session_renewal(SessionRenewalRequest(
            company_id="fenix",identity_id="id-fenix",account_id="acct-1",provider="linkedin",
            environment="PROD",version="1.0.0",authenticated=False,
            renewable_without_secret_exposure=True,higher_priority_connector_available=False,
            policy_green=True,confidence=0.99
        ))
        self.assertEqual(prod["status"],"GREEN")
        self.assertFalse(prod["renewal_allowed"])
        self.assertFalse(prod["production_renewal_allowed"])

    def test_execution_guard_requires_kill_switch_audit_policy_and_credential_ref(self):
        blocked=evaluate_execution_guard(ExecutionGuardRequest(
            company_id="fenix",engine_id="SOC-001",account_id="acct-1",environment="LAB",version="1.0.0",
            action="PUBLISH_DRAFT",kill_switch_enabled=False,audit_sink_available=True,policy_green=True,
            idempotency_key="idem-1",credential_reference_available=True
        ))
        self.assertEqual(blocked["status"],"BLOCKED")
        self.assertIn("KILL_SWITCH_REQUIRED",blocked["blockers"])
        green=evaluate_execution_guard(ExecutionGuardRequest(
            company_id="fenix",engine_id="SOC-001",account_id="acct-1",environment="LAB",version="1.0.0",
            action="PUBLISH_DRAFT",kill_switch_enabled=True,audit_sink_available=True,policy_green=True,
            idempotency_key="idem-2",credential_reference_available=True
        ))
        self.assertEqual(green["status"],"GREEN")
        self.assertTrue(green["execution_allowed"])
        self.assertTrue(green["kill_switch_required"])
        self.assertTrue(green["audit_log_required"])

    def test_execution_guard_never_auto_authorizes_prod(self):
        out=evaluate_execution_guard(ExecutionGuardRequest(
            company_id="fenix",engine_id="SOC-001",account_id="acct-1",environment="PROD",version="1.0.0",
            action="PUBLISH_DRAFT",kill_switch_enabled=True,audit_sink_available=True,policy_green=True,
            idempotency_key="idem-prod",credential_reference_available=True
        ))
        self.assertEqual(out["status"],"BLOCKED")
        self.assertFalse(out["production_execution_allowed"])
        self.assertIn("PROD_EXECUTION_GATE_REQUIRED",out["blockers"])


if __name__ == "__main__":
    unittest.main()
