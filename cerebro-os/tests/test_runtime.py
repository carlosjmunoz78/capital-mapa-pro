import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from contracts import EventEnvelope, AuditRecord
from queue import Job, JobQueue

class RuntimeTests(unittest.TestCase):
    def test_event_has_multicompany_contract(self):
        event = EventEnvelope(event_type="engine.test", engine_id="EVT-001", company_id="fenix-capital", payload={"ok": True})
        data = event.to_dict()
        self.assertEqual(data["company_id"], "fenix-capital")
        self.assertEqual(data["environment"], "LAB")
        self.assertTrue(data["request_id"])
        with self.assertRaises(ValueError):
            EventEnvelope(event_type="engine.test", engine_id="EVT-001", company_id="fenix-capital", environment="DEV").to_dict()

    def test_queue_is_idempotent_within_full_runtime_scope(self):
        q = JobQueue()
        job = Job(job_id="J1", request_id="R1", company_id="A", engine_id="JOB-001", action="test", payload={})
        self.assertTrue(q.enqueue(job))
        self.assertFalse(q.enqueue(job))
        other_tenant = Job(job_id="J1", request_id="R2", company_id="B", engine_id="JOB-001", action="test", payload={})
        self.assertTrue(q.enqueue(other_tenant))
        other_env = Job(job_id="J1", request_id="R3", company_id="A", engine_id="JOB-001", action="test", payload={}, environment="PROD", version="2.0.0")
        self.assertTrue(q.enqueue(other_env))
        other_version = Job(job_id="J1", request_id="R4", company_id="A", engine_id="JOB-001", action="test", payload={}, environment="LAB", version="2.0.0")
        self.assertTrue(q.enqueue(other_version))
        self.assertEqual(len(q), 4)

    def test_queue_rejects_invalid_scope(self):
        q = JobQueue()
        with self.assertRaises(ValueError):
            q.enqueue(Job(job_id="J", request_id="R", company_id="A", engine_id="JOB-001", action="test", payload={}, environment="DEV"))
        with self.assertRaises(ValueError):
            q.enqueue(Job(job_id="J", request_id="R", company_id="A", engine_id="JOB-001", action="test", payload={}, version=""))

    def test_retry_stops_at_limit(self):
        q = JobQueue()
        job = Job(job_id="J2", request_id="R2", company_id="A", engine_id="JOB-001", action="test", payload={}, max_attempts=2)
        q.enqueue(job)
        first = q.pop()
        self.assertTrue(q.retry(first))
        second = q.pop()
        self.assertFalse(q.retry(second))

    def test_audit_contract_includes_cost_policy_and_evidence(self):
        with self.assertRaises(ValueError):
            AuditRecord(request_id="R", company_id="A", engine_id="AUD-001", version="0.1.0", environment="LAB", action="x", policy_result="ALLOW", result="SUCCESS", duration_ms=1).to_dict()
        record = AuditRecord(request_id="R", company_id="A", engine_id="AUD-001", version="0.1.0", environment="LAB", action="x", policy_result="ALLOW", result="SUCCESS", duration_ms=1, evidence_ref="ci://run/1")
        data = record.to_dict()
        self.assertEqual(data["cost_eur"], 0.0)
        self.assertEqual(data["policy_result"], "ALLOW")
        self.assertEqual(data["evidence_ref"], "ci://run/1")

if __name__ == "__main__":
    unittest.main()
