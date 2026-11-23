import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runtime.onboarding_queue import OnboardingQueue
from jobs.run_company_onboarding_worker import process_one

class OnboardingClaimFencingCP77(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"queue.sqlite3"
        self.q=OnboardingQueue(self.path)
        self.q.enqueue(request_id="cp77",company_id="fenix",version="1.0.0",
                       payload={"company_id":"fenix","version":"1.0.0","environment":"LAB"},
                       now_epoch=1)
    def tearDown(self):
        self.tmp.cleanup()
    def claim(self,at=2,lease=5):
        return self.q.claim(now_epoch=at,lease_seconds=lease)
    def test_stale_claim_cannot_complete_after_reclaim(self):
        old=self.claim()
        current=self.claim(at=8)
        self.assertEqual(old.attempts,1)
        self.assertEqual(current.attempts,2)
        with self.assertRaisesRegex(PermissionError,"stale"):
            self.q.complete(request_id="cp77",status="COMPLETED",result={"company_id":"fenix"},
                            now_epoch=8,claim_attempts=old.attempts)
        self.assertEqual(self.q.get("cp77").attempts,2)
        self.assertEqual(self.q.get("cp77").status,"IN_PROGRESS")
        self.q.complete(request_id="cp77",status="WAITING",result={"company_id":"fenix"},
                        now_epoch=9,claim_attempts=current.attempts)
        self.assertEqual(self.q.get("cp77").status,"WAITING")
    def test_stale_claim_cannot_retry_after_reclaim(self):
        old=self.claim()
        current=self.claim(at=8)
        with self.assertRaisesRegex(PermissionError,"stale"):
            self.q.retry_or_dead_letter(request_id="cp77",result={"company_id":"fenix"},now_epoch=8,
                                        claim_attempts=old.attempts)
        self.assertEqual(self.q.get("cp77").status,"IN_PROGRESS")
        self.assertEqual(self.q.get("cp77").attempts,current.attempts)
    def test_stale_claim_cannot_dead_letter_after_reclaim(self):
        old=self.claim()
        self.claim(at=8)
        with self.assertRaisesRegex(PermissionError,"stale"):
            self.q.retry_or_dead_letter(request_id="cp77",result={"company_id":"fenix"},
                                        now_epoch=8,max_attempts=2,claim_attempts=old.attempts)
        self.assertEqual(self.q.get("cp77").status,"IN_PROGRESS")
    def test_unclaimed_completion_rejected_without_write(self):
        with self.assertRaisesRegex(PermissionError,"active claim"):
            self.q.complete(request_id="cp77",status="COMPLETED",result={"company_id":"fenix"},now_epoch=2,claim_attempts=1)
        self.assertEqual(self.q.get("cp77").status,"QUEUED")
    def test_completed_claim_cannot_be_reopened(self):
        claimed=self.claim()
        self.q.complete(request_id="cp77",status="COMPLETED",result={"company_id":"fenix"},
                        now_epoch=3,claim_attempts=claimed.attempts)
        with self.assertRaisesRegex(PermissionError,"active claim"):
            self.q.complete(request_id="cp77",status="WAITING",result={"company_id":"fenix"},
                            now_epoch=4,claim_attempts=claimed.attempts)
        self.assertEqual(self.q.get("cp77").status,"COMPLETED")
    def test_double_retry_without_new_claim_denied(self):
        claimed=self.claim()
        self.q.retry_or_dead_letter(request_id="cp77",result={"company_id":"fenix"},
                                    now_epoch=3,claim_attempts=claimed.attempts)
        with self.assertRaisesRegex(PermissionError,"active claim"):
            self.q.retry_or_dead_letter(request_id="cp77",result={"company_id":"fenix"},
                                        now_epoch=4,claim_attempts=claimed.attempts)
        self.assertEqual(self.q.get("cp77").status,"QUEUED")
    def test_cross_company_completion_denied_atomically(self):
        claimed=self.claim()
        with self.assertRaisesRegex(ValueError,"cross-company"):
            self.q.complete(request_id="cp77",status="COMPLETED",result={"company_id":"aion"},
                            now_epoch=3,claim_attempts=claimed.attempts)
        self.assertEqual(self.q.get("cp77").status,"IN_PROGRESS")
    def test_second_connection_enforces_claim_attempts(self):
        old=self.claim()
        self.claim(at=8)
        other=OnboardingQueue(self.path)
        with self.assertRaisesRegex(PermissionError,"stale"):
            other.complete(request_id="cp77",status="COMPLETED",result={"company_id":"fenix"},
                           now_epoch=8,claim_attempts=old.attempts)
        self.assertEqual(self.q.get("cp77").status,"IN_PROGRESS")
    def test_missing_token_rejected_and_real_claim_can_complete(self):
        claimed=self.claim()
        with self.assertRaisesRegex(PermissionError,"claim_attempts required"):
            self.q.retry_or_dead_letter(request_id="cp77",result={"company_id":"fenix"},now_epoch=3)
        self.assertEqual(self.q.get("cp77").status,"IN_PROGRESS")
        self.q.retry_or_dead_letter(request_id="cp77",result={"company_id":"fenix"},
                                    now_epoch=3,claim_attempts=claimed.attempts)
        again=self.q.claim(now_epoch=65,lease_seconds=20)
        self.assertEqual(again.attempts,claimed.attempts+1)
        with self.assertRaisesRegex(PermissionError,"claim_attempts required"):
            self.q.complete(request_id="cp77",status="WAITING",
                            result={"company_id":"fenix"},now_epoch=66)
        self.q.complete(request_id="cp77",status="WAITING",result={"company_id":"fenix"},
                        now_epoch=66,claim_attempts=again.attempts)
        self.assertEqual(self.q.get("cp77").status,"WAITING")

    def test_worker_passes_real_claim_attempt(self):
        with patch("jobs.run_company_onboarding_worker.run_request",
                   return_value={"company_id":"fenix","status":"WAITING","retryable":False}):
            result=process_one(queue=self.q,now_epoch=2)
        self.assertEqual(result["decision"],"PROCESSED")
        self.assertEqual(result["attempts"],1)
        self.assertEqual(self.q.get("cp77").status,"WAITING")

if __name__=="__main__":
    unittest.main()
