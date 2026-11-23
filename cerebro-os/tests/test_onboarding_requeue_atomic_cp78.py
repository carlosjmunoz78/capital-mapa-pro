import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runtime.onboarding_queue import OnboardingQueue

class OnboardingRequeueAtomicCP78(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"onboarding.sqlite3"
        self.a=OnboardingQueue(self.path)
        self.b=OnboardingQueue(self.path)
        self.a.enqueue(request_id="rq-1",company_id="fenix",version="1.0.0",
                       payload={"company_id":"fenix","version":"1.0.0","environment":"LAB",
                                "context":{"console_context_ref":"company:fenix"}},
                       now_epoch=10)
        self.claimed=self.a.claim(now_epoch=11)
        self.a.complete(request_id="rq-1",status="WAITING",result={"company_id":"fenix"},now_epoch=12,
                        claim_attempts=self.claimed.attempts)
    def tearDown(self):
        self.tmp.cleanup()
    def payload(self,**overrides):
        p={"company_id":"fenix","version":"1.0.0","environment":"LAB",
           "context":{"console_context_ref":"company:fenix"}}
        p.update(overrides)
        return p
    def test_requeue_from_waiting_valid(self):
        self.a.requeue(request_id="rq-1",payload=self.payload(),now_epoch=20)
        self.assertEqual(self.a.get("rq-1").status,"QUEUED")
        self.assertEqual(self.a.get("rq-1").attempts,1)
    def test_other_connection_cannot_repeat_requeue(self):
        self.a.requeue(request_id="rq-1",payload=self.payload(),now_epoch=20)
        with self.assertRaisesRegex(ValueError,"only WAITING"):
            self.b.requeue(request_id="rq-1",payload=self.payload(),now_epoch=21)
        self.assertEqual(self.a.get("rq-1").updated_at_epoch if hasattr(self.a.get("rq-1"),"updated_at_epoch") else self.a.get("rq-1").status,"QUEUED")
    def test_claim_after_requeue_blocks_stale_redrive(self):
        self.a.requeue(request_id="rq-1",payload=self.payload(),now_epoch=20)
        current=self.b.claim(now_epoch=21)
        self.assertEqual(current.attempts,2)
        with self.assertRaisesRegex(ValueError,"only WAITING"):
            self.a.requeue(request_id="rq-1",payload=self.payload(),now_epoch=22)
        self.assertEqual(self.a.get("rq-1").status,"IN_PROGRESS")
    def test_cross_tenant_requeue_denied(self):
        with self.assertRaisesRegex(ValueError,"cross-company"):
            self.a.requeue(request_id="rq-1",payload=self.payload(company_id="aion"),now_epoch=20)
        self.assertEqual(self.a.get("rq-1").status,"WAITING")
    def test_cross_version_requeue_denied(self):
        with self.assertRaisesRegex(ValueError,"cross-version"):
            self.a.requeue(request_id="rq-1",payload=self.payload(version="2.0.0"),now_epoch=20)
        self.assertEqual(self.a.get("rq-1").status,"WAITING")
    def test_cross_environment_requeue_denied(self):
        with self.assertRaisesRegex(ValueError,"cross-environment"):
            self.a.requeue(request_id="rq-1",payload=self.payload(environment="PREPROD"),now_epoch=20)
        self.assertEqual(self.a.get("rq-1").status,"WAITING")
    def test_context_of_other_tenant_denied(self):
        with self.assertRaisesRegex(ValueError,"cross-company onboarding"):
            self.a.requeue(request_id="rq-1",payload=self.payload(context={"console_context_ref":"company:aion"}),now_epoch=20)
        self.assertEqual(self.a.get("rq-1").status,"WAITING")
    def test_raw_secret_denied_and_queue_unchanged(self):
        with self.assertRaisesRegex(ValueError,"raw secret"):
            self.a.requeue(request_id="rq-1",payload=self.payload(token="forbidden"),now_epoch=20)
        self.assertEqual(self.a.get("rq-1").status,"WAITING")
    def test_missing_version_environment_preserves_original_scope(self):
        self.a.requeue(request_id="rq-1",payload={"company_id":"fenix"},now_epoch=20)
        q=self.a.get("rq-1")
        self.assertEqual(q.payload["version"],"1.0.0")
        self.assertEqual(q.payload["environment"],"LAB")
    def test_invalid_context_does_not_mutate(self):
        with self.assertRaisesRegex(ValueError,"context must be object"):
            self.a.requeue(request_id="rq-1",payload=self.payload(context=[]),now_epoch=20)
        self.assertEqual(self.a.get("rq-1").status,"WAITING")
    def test_dead_letter_can_be_explicitly_requeued(self):
        q2="rq-dead"
        self.a.enqueue(request_id=q2,company_id="fenix",version="1.0.0",payload=self.payload(),now_epoch=10)
        item=self.a.claim(now_epoch=21)
        self.a.retry_or_dead_letter(request_id=item.request_id,result={"company_id":"fenix"},now_epoch=22,max_attempts=1,claim_attempts=item.attempts)
        self.a.requeue(request_id=q2,payload=self.payload(),now_epoch=23)
        self.assertEqual(self.a.get(q2).status,"QUEUED")
    def test_priority_preserved_and_validated(self):
        self.a.requeue(request_id="rq-1",payload=self.payload(),now_epoch=20,priority=255)
        self.assertEqual(self.a.get("rq-1").priority,255)

if __name__=="__main__":
    unittest.main()
