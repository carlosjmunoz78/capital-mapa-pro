import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"identity"))

from browser_bridge_protocol import BridgeDispatch,BridgeAck,BridgeCommandQueue
from browser_bridge_result_policy import evaluate_bridge_result

class BrowserBridgeProtocolTests(unittest.TestCase):
    def _dispatch(self,**overrides):
        item=dict(
            command_id="cmd-1",request_id="req-1",company_id="fenix",identity_id="id-fenix",account_id="acct-1",
            engine_id="SOC-001",capability="publish",action="PUBLISH_DRAFT",device_id="desktop-1",profile_id="chrome-1",
            environment="LAB",version="1.0.0",idempotency_key="idem-1",audit_ref="audit://1",
            created_at_epoch=100,expires_at_epoch=200
        )
        item.update(overrides); return BridgeDispatch(**item)

    def _ack(self,**overrides):
        item=dict(
            command_id="cmd-1",request_id="req-1",idempotency_key="idem-1",device_id="desktop-1",
            company_id="fenix",environment="LAB",version="1.0.0",status="COMPLETED",
            observed_at_epoch=150,evidence_ref="e://done"
        )
        item.update(overrides); return BridgeAck(**item)

    def test_queue_claims_only_matching_device_scope(self):
        q=BridgeCommandQueue()
        q.enqueue(self._dispatch())
        self.assertIsNone(q.claim(company_id="aion",device_id="desktop-1",environment="LAB",version="1.0.0",now_epoch=120))
        claimed=q.claim(company_id="fenix",device_id="desktop-1",environment="LAB",version="1.0.0",now_epoch=120)
        self.assertEqual(claimed.command_id,"cmd-1")
        self.assertEqual(q.command_status("cmd-1"),"CLAIMED")

    def test_expired_command_is_not_claimed(self):
        q=BridgeCommandQueue(); q.enqueue(self._dispatch(expires_at_epoch=110))
        claimed=q.claim(company_id="fenix",device_id="desktop-1",environment="LAB",version="1.0.0",now_epoch=120)
        self.assertIsNone(claimed)
        self.assertEqual(q.command_status("cmd-1"),"EXPIRED")

    def test_idempotency_key_prevents_duplicate_commands(self):
        q=BridgeCommandQueue(); q.enqueue(self._dispatch())
        with self.assertRaisesRegex(ValueError,"duplicate idempotency"):
            q.enqueue(self._dispatch(command_id="cmd-2"))

    def test_ack_scope_mismatch_is_rejected(self):
        q=BridgeCommandQueue(); q.enqueue(self._dispatch())
        q.claim(company_id="fenix",device_id="desktop-1",environment="LAB",version="1.0.0",now_epoch=120)
        with self.assertRaisesRegex(PermissionError,"scope mismatch"):
            q.acknowledge(self._ack(company_id="aion"))

    def test_terminal_ack_is_idempotent_for_same_result(self):
        q=BridgeCommandQueue(); q.enqueue(self._dispatch())
        q.claim(company_id="fenix",device_id="desktop-1",environment="LAB",version="1.0.0",now_epoch=120)
        ack=self._ack()
        q.acknowledge(ack); q.acknowledge(ack)
        self.assertEqual(q.command_status("cmd-1"),"COMPLETED")

    def test_completed_result_requires_evidence_and_expected_side_effect(self):
        missing=evaluate_bridge_result(command_status="COMPLETED",evidence_ref="",side_effect_reported=True,expected_side_effect=True)
        self.assertEqual(missing["decision"],"COMPLETION_EVIDENCE_REQUIRED")
        mismatch=evaluate_bridge_result(command_status="COMPLETED",evidence_ref="e://done",side_effect_reported=False,expected_side_effect=True)
        self.assertEqual(mismatch["decision"],"EXPECTED_SIDE_EFFECT_NOT_CONFIRMED")
        green=evaluate_bridge_result(command_status="COMPLETED",evidence_ref="e://done",side_effect_reported=True,expected_side_effect=True)
        self.assertEqual(green["status"],"GREEN")
        self.assertTrue(green["promotion_allowed"])

    def test_unexpected_side_effect_becomes_security_incident(self):
        out=evaluate_bridge_result(command_status="COMPLETED",evidence_ref="e://done",side_effect_reported=True,expected_side_effect=False)
        self.assertEqual(out["status"],"HUMAN_REQUIRED")
        self.assertEqual(out["human_reason"],"SECURITY_INCIDENT")
        self.assertFalse(out["promotion_allowed"])

if __name__=="__main__":
    unittest.main()
