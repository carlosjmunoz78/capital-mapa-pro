import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runtime.onboarding_queue import OnboardingQueue

class OnboardingMandatoryClaimCP80(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"q.sqlite3"
        self.q=OnboardingQueue(self.path)
        self.q.enqueue(request_id="fence",company_id="fenix",version="1.0.0",
            payload={"company_id":"fenix","environment":"LAB"},now_epoch=1)
        self.claim=self.q.claim(now_epoch=2,lease_seconds=10)
    def tearDown(self):self.tmp.cleanup()
    def test_completion_without_attempt_denied_and_state_preserved(self):
        with self.assertRaisesRegex(PermissionError,"claim_attempts required"):
            self.q.complete(request_id="fence",status="WAITING",result={"company_id":"fenix"},now_epoch=3)
        self.assertEqual(self.q.get("fence").status,"IN_PROGRESS")
    def test_retry_without_attempt_denied_and_state_preserved(self):
        with self.assertRaisesRegex(PermissionError,"claim_attempts required"):
            self.q.retry_or_dead_letter(request_id="fence",result={"company_id":"fenix"},now_epoch=3)
        self.assertEqual(self.q.get("fence").status,"IN_PROGRESS")
    def test_dead_letter_without_attempt_denied(self):
        with self.assertRaisesRegex(PermissionError,"claim_attempts required"):
            self.q.retry_or_dead_letter(request_id="fence",result={"company_id":"fenix"},
                                        now_epoch=3,max_attempts=1)
        self.assertEqual(self.q.get("fence").status,"IN_PROGRESS")
    def test_invalid_tokens_rejected(self):
        for token in (0,-1,True,"1",1.0):
            with self.subTest(token=token):
                with self.assertRaisesRegex(PermissionError,"claim_attempts required"):
                    self.q.complete(request_id="fence",status="WAITING",result={"company_id":"fenix"},
                                    now_epoch=3,claim_attempts=token)
                self.assertEqual(self.q.get("fence").status,"IN_PROGRESS")
    def test_actual_claim_completes(self):
        self.q.complete(request_id="fence",status="WAITING",result={"company_id":"fenix"},
                        now_epoch=3,claim_attempts=self.claim.attempts)
        self.assertEqual(self.q.get("fence").status,"WAITING")
    def test_stale_worker_without_token_cannot_clobber_recovered(self):
        newer=self.q.claim(now_epoch=13)
        self.assertEqual(newer.attempts,2)
        with self.assertRaisesRegex(PermissionError,"claim_attempts required"):
            self.q.complete(request_id="fence",status="BLOCKED",
                            result={"company_id":"fenix"},now_epoch=14)
        self.assertEqual(self.q.get("fence").attempts,2)
        self.assertEqual(self.q.get("fence").status,"IN_PROGRESS")
    def test_atomic_retry_with_actual_token(self):
        out=self.q.retry_or_dead_letter(request_id="fence",result={"company_id":"fenix"},
                                        now_epoch=3,claim_attempts=self.claim.attempts)
        self.assertEqual(out["status"],"RETRY_SCHEDULED")
        self.assertEqual(self.q.get("fence").status,"QUEUED")

if __name__=="__main__":unittest.main()
