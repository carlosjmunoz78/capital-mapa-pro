import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"identity"))

from browser_bridge_runtime import BridgeHeartbeat,DispatchReceipt,BridgeRuntimeState,evaluate_bridge_runtime_dispatch

class BrowserBridgeRuntimeTests(unittest.TestCase):
    def _state(self,observed_at=100,**overrides):
        hb=dict(
            device_id="desktop-1",company_id="fenix",profile_id="chrome-1",environment="LAB",version="1.0.0",
            observed_at_epoch=observed_at,online=True,paired=True,kill_switch_enabled=True
        )
        hb.update(overrides)
        state=BridgeRuntimeState(); state.record_heartbeat(BridgeHeartbeat(**hb)); return state

    def _command(self,**overrides):
        cmd={"company_id":"fenix","device_id":"desktop-1","environment":"LAB","version":"1.0.0","idempotency_key":"idem-1"}
        cmd.update(overrides); return cmd

    def test_fresh_heartbeat_allows_nonprod_dispatch(self):
        out=evaluate_bridge_runtime_dispatch(state=self._state(),command=self._command(),now_epoch=150,max_heartbeat_age_seconds=60)
        self.assertEqual(out["status"],"GREEN")
        self.assertTrue(out["dispatch_allowed"])
        self.assertTrue(out["receipt_required"])
        self.assertTrue(out["audit_log_required"])

    def test_missing_stale_offline_and_kill_switch_fail_closed(self):
        empty=evaluate_bridge_runtime_dispatch(state=BridgeRuntimeState(),command=self._command(),now_epoch=150)
        self.assertEqual(empty["decision"],"HEARTBEAT_MISSING")
        stale=evaluate_bridge_runtime_dispatch(state=self._state(observed_at=1),command=self._command(),now_epoch=150,max_heartbeat_age_seconds=60)
        self.assertEqual(stale["decision"],"HEARTBEAT_STALE")
        offline=evaluate_bridge_runtime_dispatch(state=self._state(online=False),command=self._command(),now_epoch=150)
        self.assertEqual(offline["decision"],"BRIDGE_OFFLINE")
        killed=evaluate_bridge_runtime_dispatch(state=self._state(kill_switch_enabled=False),command=self._command(),now_epoch=150)
        self.assertEqual(killed["decision"],"KILL_SWITCH_REQUIRED")

    def test_stale_heartbeat_update_is_rejected(self):
        state=self._state(observed_at=100)
        with self.assertRaisesRegex(ValueError,"stale heartbeat"):
            state.record_heartbeat(BridgeHeartbeat(
                device_id="desktop-1",company_id="fenix",profile_id="chrome-1",environment="LAB",version="1.0.0",
                observed_at_epoch=99,online=True,paired=True,kill_switch_enabled=True
            ))

    def test_completed_receipt_suppresses_duplicate_dispatch(self):
        state=self._state()
        state.record_receipt(DispatchReceipt(
            request_id="req-1",idempotency_key="idem-1",device_id="desktop-1",company_id="fenix",
            environment="LAB",version="1.0.0",status="COMPLETED",observed_at_epoch=120,evidence_ref="e://done"
        ))
        out=evaluate_bridge_runtime_dispatch(state=state,command=self._command(),now_epoch=150)
        self.assertEqual(out["decision"],"IDEMPOTENT_REPLAY_SUPPRESSED")
        self.assertFalse(out["dispatch_allowed"])
        self.assertEqual(out["receipt_evidence_ref"],"e://done")

    def test_idempotency_conflict_is_rejected(self):
        state=self._state()
        state.record_receipt(DispatchReceipt(
            request_id="req-1",idempotency_key="idem-1",device_id="desktop-1",company_id="fenix",
            environment="LAB",version="1.0.0",status="ACKNOWLEDGED",observed_at_epoch=120
        ))
        with self.assertRaisesRegex(ValueError,"idempotency key conflict"):
            state.record_receipt(DispatchReceipt(
                request_id="req-2",idempotency_key="idem-1",device_id="desktop-1",company_id="fenix",
                environment="LAB",version="1.0.0",status="ACKNOWLEDGED",observed_at_epoch=121
            ))

    def test_prod_runtime_dispatch_is_high_risk(self):
        state=self._state(environment="PROD")
        out=evaluate_bridge_runtime_dispatch(
            state=state,command=self._command(environment="PROD"),now_epoch=150,max_heartbeat_age_seconds=60
        )
        self.assertEqual(out["status"],"HUMAN_REQUIRED")
        self.assertEqual(out["human_reason"],"HIGH_RISK")
        self.assertFalse(out["dispatch_allowed"])

if __name__=="__main__":
    unittest.main()
