import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from runtime.onboarding_queue import OnboardingQueue
from jobs.run_company_onboarding_worker import process_one

class OnboardingQueueWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/"queue.sqlite3"
        self.queue=OnboardingQueue(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def _payload(self):
        return {
          "company_id":"fenix","version":"1.0.0","max_steps":10,
          "context":{
            "company_profile":{"legal_name":"Fenix Test","evidence_ref":"doc://company"},
            "access_requirements":[{"capability":"crm","purpose":"sales","provider":"existing","required":True}],
            "existing_accounts":[{"company_id":"fenix","account_id":"acct-1","capabilities":["crm"]}],
            "existing_connectors":[],"session_observations":[],"domains":[],
          }
        }

    def test_queue_claims_and_worker_processes_without_manual_ok(self):
        self.queue.enqueue(request_id="req-1",company_id="fenix",version="1.0.0",payload=self._payload(),now_epoch=100)
        out=process_one(queue=self.queue,now_epoch=110,lease_seconds=30)
        self.assertTrue(out["processed"])
        self.assertEqual(out["status"],"WAITING")
        row=self.queue.get("req-1")
        self.assertEqual(row.status,"WAITING")
        self.assertEqual(row.attempts,1)
        self.assertEqual(row.last_result["state"]["current_phase"],"SCAN_DIGITAL_FOOTPRINT")
        self.assertFalse(row.last_result["production_activation_allowed"])

    def test_empty_queue_returns_no_work(self):
        out=process_one(queue=self.queue,now_epoch=100)
        self.assertEqual(out["decision"],"NO_WORK")
        self.assertFalse(out["processed"])

    def test_stale_lease_can_be_reclaimed_after_worker_loss(self):
        self.queue.enqueue(request_id="req-1",company_id="fenix",version="1.0.0",payload=self._payload(),now_epoch=100)
        first=self.queue.claim(now_epoch=110,lease_seconds=10)
        self.assertEqual(first.status,"IN_PROGRESS")
        self.assertIsNone(self.queue.claim(now_epoch=115,lease_seconds=10))
        second=self.queue.claim(now_epoch=121,lease_seconds=10)
        self.assertIsNotNone(second)
        self.assertEqual(second.attempts,2)

    def test_raw_secret_fields_are_rejected_before_queue_storage(self):
        payload=self._payload()
        payload["context"]["password"]="never-store-me"
        with self.assertRaisesRegex(ValueError,"raw secret field forbidden"):
            self.queue.enqueue(request_id="req-1",company_id="fenix",version="1.0.0",payload=payload,now_epoch=100)

    def test_cross_company_queue_payload_is_denied(self):
        payload=self._payload()
        payload["company_id"]="aion"
        with self.assertRaisesRegex(ValueError,"cross-company queue payload"):
            self.queue.enqueue(request_id="req-1",company_id="fenix",version="1.0.0",payload=payload,now_epoch=100)

    def test_waiting_request_can_be_requeued_with_new_evidence(self):
        self.queue.enqueue(request_id="req-1",company_id="fenix",version="1.0.0",payload=self._payload(),now_epoch=100)
        process_one(queue=self.queue,now_epoch=110)
        payload=self._payload()
        payload["context"]["domains"]=[]
        self.queue.requeue(request_id="req-1",payload=payload,now_epoch=120)
        self.assertEqual(self.queue.get("req-1").status,"QUEUED")
        out=process_one(queue=self.queue,now_epoch=130)
        self.assertTrue(out["processed"])
        self.assertEqual(self.queue.get("req-1").attempts,2)

if __name__=="__main__":
    unittest.main()
