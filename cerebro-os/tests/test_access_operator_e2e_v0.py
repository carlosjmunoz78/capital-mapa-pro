import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"identity"))

from account_registry import IdentityRecord,AccountRecord,IdentityAccountRegistry
from credential_scope import ScopedCredentialRef
from connector_registry import ConnectorCapability,ConnectorRegistry
from multiaccount_session_registry import SessionBinding,MultiAccountSessionRegistry
from browser_bridge_control import BrowserBridgeDevice,BrowserBridgeRegistry
from browser_bridge_runtime import BridgeHeartbeat,BridgeRuntimeState
from access_operator import AccessOperationRequest,plan_access_operation

class AccessOperatorE2ETests(unittest.TestCase):
    def _base(self,connector_type="COMPUTER_USE",with_session=True,environment="LAB"):
        accounts=IdentityAccountRegistry()
        accounts.register_identity(IdentityRecord("id-fenix","COMPANY","fenix","fenix","Fenix","default",environment,"1.0.0"))
        accounts.register_account(AccountRecord(
            "acct-1","id-fenix","fenix","linkedin","ops@fenix.example","OAUTH","marketing",environment,"1.0.0"
        ))
        credential=ScopedCredentialRef(
            credential_ref_id="cred-1",account_id="acct-1",identity_id="id-fenix",company_id="fenix",
            vault_provider="GITHUB_SECRETS",secret_ref="FENIX_LINKEDIN_OAUTH",environment=environment,version="1.0.0"
        )
        connectors=ConnectorRegistry()
        connectors.register(ConnectorCapability("conn-1","fenix","publish",connector_type,environment,True,"1.0.0"))

        sessions=MultiAccountSessionRegistry()
        if with_session:
            sessions.register(SessionBinding(
                "sess-1","fenix","id-fenix","acct-1","linkedin","chrome-1","desktop-1","CHROME",
                environment,"1.0.0",True,"e://session"
            ))

        bridges=BrowserBridgeRegistry()
        bridges.register(BrowserBridgeDevice(
            "desktop-1","fenix","chrome-1","CHROME",environment,"1.0.0",True,True,True
        ))

        runtime=BridgeRuntimeState()
        runtime.record_heartbeat(BridgeHeartbeat(
            "desktop-1","fenix","chrome-1",environment,"1.0.0",100,True,True,True
        ))
        return accounts,credential,connectors,sessions,bridges,runtime

    def _request(self,environment="LAB"):
        return AccessOperationRequest(
            request_id="req-1",company_id="fenix",identity_id="id-fenix",account_id="acct-1",
            engine_id="SOC-001",capability="publish",action="PUBLISH_DRAFT",environment=environment,
            version="1.0.0",idempotency_key="idem-1",audit_ref="audit://1",policy_green=True,confidence=0.95
        )

    def test_official_connector_wins_without_browser_dispatch(self):
        deps=self._base(connector_type="OFFICIAL_API")
        out=plan_access_operation(
            self._request(),
            account_registry=deps[0],credential=deps[1],connectors=deps[2],sessions=deps[3],
            bridge_registry=deps[4],runtime_state=deps[5],now_epoch=150
        )
        self.assertEqual(out["status"],"GREEN")
        self.assertEqual(out["decision"],"CONNECTOR_EXECUTION_CANDIDATE")
        self.assertEqual(out["connector_type"],"OFFICIAL_API")
        self.assertIsNone(out["dispatch_candidate"])
        self.assertFalse(out["external_mutation_performed"])

    def test_browser_fallback_builds_dispatch_candidate_only_when_every_gate_is_green(self):
        deps=self._base()
        out=plan_access_operation(
            self._request(),
            account_registry=deps[0],credential=deps[1],connectors=deps[2],sessions=deps[3],
            bridge_registry=deps[4],runtime_state=deps[5],now_epoch=150
        )
        self.assertEqual(out["status"],"GREEN")
        self.assertEqual(out["decision"],"BRIDGE_DISPATCH_CANDIDATE")
        self.assertEqual(out["dispatch_candidate"]["device_id"],"desktop-1")
        self.assertEqual(out["dispatch_candidate"]["profile_id"],"chrome-1")
        self.assertFalse(out["credential_value_included"])
        self.assertFalse(out["secret_value_included"])
        self.assertFalse(out["external_mutation_performed"])

    def test_browser_fallback_blocks_without_authenticated_session(self):
        deps=self._base(with_session=False)
        out=plan_access_operation(
            self._request(),
            account_registry=deps[0],credential=deps[1],connectors=deps[2],sessions=deps[3],
            bridge_registry=deps[4],runtime_state=deps[5],now_epoch=150
        )
        self.assertEqual(out["status"],"BLOCKED")
        self.assertEqual(out["decision"],"AUTHENTICATED_SESSION_REQUIRED")
        self.assertIsNone(out["dispatch_candidate"])

    def test_browser_fallback_blocks_when_runtime_heartbeat_is_stale(self):
        deps=self._base()
        out=plan_access_operation(
            self._request(),
            account_registry=deps[0],credential=deps[1],connectors=deps[2],sessions=deps[3],
            bridge_registry=deps[4],runtime_state=deps[5],now_epoch=500,max_heartbeat_age_seconds=60
        )
        self.assertEqual(out["status"],"BLOCKED")
        self.assertEqual(out["decision"],"BRIDGE_RUNTIME_NOT_READY")
        self.assertEqual(out["runtime"]["decision"],"HEARTBEAT_STALE")

    def test_prod_connector_execution_is_fail_closed_high_risk(self):
        deps=self._base(connector_type="OFFICIAL_API",environment="PROD")
        out=plan_access_operation(
            self._request(environment="PROD"),
            account_registry=deps[0],credential=deps[1],connectors=deps[2],sessions=deps[3],
            bridge_registry=deps[4],runtime_state=deps[5],now_epoch=150
        )
        self.assertEqual(out["status"],"HUMAN_REQUIRED")
        self.assertEqual(out["decision"],"PROD_CONNECTOR_EXECUTION_GATE_REQUIRED")
        self.assertEqual(out["human_reason"],"HIGH_RISK")

    def test_cross_identity_account_mismatch_fails_closed(self):
        deps=self._base()
        bad=AccessOperationRequest(
            request_id="req-2",company_id="fenix",identity_id="other-id",account_id="acct-1",
            engine_id="SOC-001",capability="publish",action="PUBLISH_DRAFT",environment="LAB",
            version="1.0.0",idempotency_key="idem-2",audit_ref="audit://2",policy_green=True,confidence=0.95
        )
        with self.assertRaisesRegex(PermissionError,"identity/account mismatch"):
            plan_access_operation(
                bad,account_registry=deps[0],credential=deps[1],connectors=deps[2],sessions=deps[3],
                bridge_registry=deps[4],runtime_state=deps[5],now_epoch=150
            )

if __name__=="__main__":
    unittest.main()
