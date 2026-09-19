import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"identity"))

from browser_bridge_control import BrowserBridgeDevice,BrowserBridgeCommand,BrowserBridgeRegistry,evaluate_bridge_command
from browser_bridge_handoff import build_bridge_handoff

class BrowserBridgeControlTests(unittest.TestCase):
    def _registry(self,**overrides):
        item=dict(
            device_id="desktop-1",company_id="fenix",profile_id="chrome-1",browser_family="CHROME",
            environment="LAB",version="1.0.0",paired=True,online=True,kill_switch_enabled=True
        )
        item.update(overrides)
        r=BrowserBridgeRegistry(); r.register(BrowserBridgeDevice(**item)); return r

    def _command(self,**overrides):
        item=dict(
            request_id="req-1",company_id="fenix",identity_id="id-fenix",account_id="acct-1",
            engine_id="SOC-001",capability="publish",action="PUBLISH_DRAFT",device_id="desktop-1",
            profile_id="chrome-1",environment="LAB",version="1.0.0",idempotency_key="idem-1",
            audit_ref="audit://1",policy_green=True,confidence=0.95,credential_reference_available=True
        )
        item.update(overrides); return BrowserBridgeCommand(**item)

    def test_bridge_command_requires_registered_paired_online_kill_switch_device(self):
        out=evaluate_bridge_command(self._command(),self._registry())
        self.assertEqual(out["status"],"GREEN")
        self.assertTrue(out["dispatch_allowed"])
        self.assertTrue(out["kill_switch_required"])
        self.assertTrue(out["audit_log_required"])
        self.assertFalse(out["credential_value_exposure_allowed"])

    def test_bridge_command_blocks_offline_or_unpaired_device(self):
        offline=evaluate_bridge_command(self._command(),self._registry(online=False))
        self.assertEqual(offline["status"],"BLOCKED")
        self.assertIn("BRIDGE_OFFLINE",offline["blockers"])
        unpaired=evaluate_bridge_command(self._command(),self._registry(paired=False))
        self.assertIn("BRIDGE_NOT_PAIRED",unpaired["blockers"])

    def test_bridge_command_is_company_profile_scoped(self):
        out=evaluate_bridge_command(self._command(company_id="aion"),self._registry())
        self.assertEqual(out["decision"],"BRIDGE_DEVICE_NOT_REGISTERED")
        self.assertFalse(out["dispatch_allowed"])

    def test_bridge_command_prod_is_high_risk_and_fail_closed(self):
        reg=self._registry(environment="PROD")
        out=evaluate_bridge_command(self._command(environment="PROD"),reg)
        self.assertEqual(out["status"],"HUMAN_REQUIRED")
        self.assertEqual(out["human_reason"],"HIGH_RISK")
        self.assertFalse(out["dispatch_allowed"])
        self.assertIn("PROD_BRIDGE_EXECUTION_GATE_REQUIRED",out["blockers"])

    def test_handoff_requires_green_access_authenticated_session_and_guard(self):
        access={
            "status":"GREEN","decision":"COMPUTER_USE_FALLBACK","company_id":"fenix","identity_id":"id-fenix",
            "account_id":"acct-1","engine_id":"SOC-001","capability":"publish","action":"PUBLISH_DRAFT",
            "environment":"LAB","version":"1.0.0","credential_reference_available":True,"confidence":0.95
        }
        session={"company_id":"fenix","account_id":"acct-1","authenticated":True,"profile_id":"chrome-1","device_id":"desktop-1"}
        guard={"company_id":"fenix","account_id":"acct-1","status":"GREEN","execution_allowed":True,"idempotency_key":"idem-1"}
        out=build_bridge_handoff(access_plan=access,session=session,guard=guard,request_id="req-1",audit_ref="audit://1")
        self.assertEqual(out["status"],"GREEN")
        self.assertEqual(out["dispatch_candidate"]["profile_id"],"chrome-1")
        self.assertFalse(out["credential_value_included"])
        self.assertFalse(out["secret_value_included"])

    def test_handoff_rejects_cross_account_or_unauthenticated_session(self):
        access={
            "status":"GREEN","decision":"COMPUTER_USE_FALLBACK","company_id":"fenix","identity_id":"id-fenix",
            "account_id":"acct-1","engine_id":"SOC-001","capability":"publish","action":"PUBLISH_DRAFT",
            "environment":"LAB","version":"1.0.0","credential_reference_available":True
        }
        guard={"company_id":"fenix","account_id":"acct-1","status":"GREEN","execution_allowed":True,"idempotency_key":"idem-1"}
        blocked=build_bridge_handoff(
            access_plan=access,
            session={"company_id":"fenix","account_id":"acct-1","authenticated":False,"profile_id":"chrome-1","device_id":"desktop-1"},
            guard=guard,request_id="req-1",audit_ref="audit://1"
        )
        self.assertEqual(blocked["reason"],"AUTHENTICATED_SESSION_REQUIRED")
        with self.assertRaisesRegex(ValueError,"cross-account"):
            build_bridge_handoff(
                access_plan=access,
                session={"company_id":"fenix","account_id":"acct-2","authenticated":True,"profile_id":"chrome-1","device_id":"desktop-1"},
                guard=guard,request_id="req-2",audit_ref="audit://2"
            )

if __name__=="__main__":
    unittest.main()
