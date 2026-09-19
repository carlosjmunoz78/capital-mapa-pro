import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"identity"))

from browser_bridge_protocol import BridgeDispatch,BridgeCommandQueue
from browser_bridge_worker import WorkerIdentity,execute_one

class BrowserBridgeWorkerTests(unittest.TestCase):
    def _queue(self,environment="LAB"):
        q=BridgeCommandQueue()
        q.enqueue(BridgeDispatch(
            command_id="cmd-1",request_id="req-1",company_id="fenix",identity_id="id-fenix",account_id="acct-1",
            engine_id="SOC-001",capability="publish",action="PUBLISH_DRAFT",device_id="desktop-1",profile_id="chrome-1",
            environment=environment,version="1.0.0",idempotency_key="idem-1",audit_ref="audit://1",
            created_at_epoch=100,expires_at_epoch=200
        ))
        return q

    def test_worker_passes_only_safe_metadata_to_executor_and_accepts_evidence(self):
        q=self._queue()
        seen=[]
        def executor(payload):
            seen.append(payload)
            return {"status":"COMPLETED","evidence_ref":"e://done","side_effect_reported":True,"expected_side_effect":True}
        out=execute_one(
            worker=WorkerIdentity("fenix","desktop-1","LAB","1.0.0"),
            queue=q,executor=executor,now_epoch=150
        )
        self.assertEqual(out["status"],"GREEN")
        self.assertEqual(out["decision"],"COMMAND_EVIDENCE_ACCEPTED")
        self.assertTrue(out["promotion_allowed"])
        self.assertEqual(q.command_status("cmd-1"),"COMPLETED")
        self.assertNotIn("password",seen[0])
        self.assertNotIn("token",seen[0])
        self.assertNotIn("secret",seen[0])
        self.assertFalse(out["executor_payload_contains_secret"])
        self.assertFalse(out["executor_payload_contains_credential_value"])

    def test_worker_failure_does_not_promote(self):
        q=self._queue()
        out=execute_one(
            worker=WorkerIdentity("fenix","desktop-1","LAB","1.0.0"),
            queue=q,executor=lambda payload: {"status":"FAILED","evidence_ref":"e://failure","side_effect_reported":False},
            now_epoch=150
        )
        self.assertEqual(out["status"],"BLOCKED")
        self.assertFalse(out["promotion_allowed"])
        self.assertEqual(q.command_status("cmd-1"),"FAILED")

    def test_worker_exception_is_sanitized_and_fails_closed(self):
        q=self._queue()
        def boom(payload):
            raise RuntimeError("password=do-not-leak")
        out=execute_one(
            worker=WorkerIdentity("fenix","desktop-1","LAB","1.0.0"),
            queue=q,executor=boom,now_epoch=150
        )
        self.assertEqual(out["status"],"BLOCKED")
        self.assertEqual(out["evidence_ref"],"")
        self.assertFalse(out["promotion_allowed"])

    def test_wrong_device_claims_nothing(self):
        q=self._queue()
        out=execute_one(
            worker=WorkerIdentity("fenix","desktop-2","LAB","1.0.0"),
            queue=q,executor=lambda payload: {"status":"COMPLETED"},
            now_epoch=150
        )
        self.assertEqual(out["decision"],"NO_COMMAND")
        self.assertFalse(out["claimed"])
        self.assertEqual(q.command_status("cmd-1"),"QUEUED")

    def test_prod_worker_is_disabled_v0(self):
        q=self._queue(environment="PROD")
        out=execute_one(
            worker=WorkerIdentity("fenix","desktop-1","PROD","1.0.0"),
            queue=q,executor=lambda payload: {"status":"COMPLETED"},
            now_epoch=150
        )
        self.assertEqual(out["status"],"HUMAN_REQUIRED")
        self.assertEqual(out["human_reason"],"HIGH_RISK")
        self.assertFalse(out["executed"])
        self.assertEqual(q.command_status("cmd-1"),"QUEUED")

if __name__=="__main__":
    unittest.main()
