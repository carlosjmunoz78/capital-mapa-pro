import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runtime.onboarding_queue import OnboardingQueue

SOURCE={"type":"CEREBRO_CONSOLE","user_id":"CARLOS","request_id":"verified-r1"}
CONTEXT={"console_context_ref":"company:fenix","classification":"verified"}
class OnboardingRedriveProvenanceCP79(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"q.sqlite3"
        self.q=OnboardingQueue(self.path)
        self.q.enqueue(request_id="verified-r1",company_id="fenix",version="1.0.0",
            payload={"company_id":"fenix","version":"1.0.0","environment":"LAB",
                     "source":SOURCE,"context":CONTEXT},
            now_epoch=1)
        item=self.q.claim(now_epoch=2)
        self.q.complete(request_id="verified-r1",status="WAITING",
            result={"company_id":"fenix"},now_epoch=3,claim_attempts=item.attempts)
    def tearDown(self):
        self.tmp.cleanup()
    def test_partial_payload_preserves_source_and_context(self):
        self.q.requeue(request_id="verified-r1",payload={"company_id":"fenix"},now_epoch=4)
        item=self.q.get("verified-r1")
        self.assertEqual(item.payload["source"],SOURCE)
        self.assertEqual(item.payload["context"],CONTEXT)
        self.assertEqual(item.status,"QUEUED")
    def test_metadata_merge_preserves_original_context_reference(self):
        self.q.requeue(request_id="verified-r1",
            payload={"company_id":"fenix","context":{"new_evidence":"receipt-1"}},now_epoch=4)
        context=self.q.get("verified-r1").payload["context"]
        self.assertEqual(context["console_context_ref"],"company:fenix")
        self.assertEqual(context["classification"],"verified")
        self.assertEqual(context["new_evidence"],"receipt-1")
    def test_other_user_source_denied_without_mutation(self):
        bad={**SOURCE,"user_id":"IMPOSTOR"}
        with self.assertRaisesRegex(ValueError,"source immutable"):
            self.q.requeue(request_id="verified-r1",payload={"company_id":"fenix","source":bad},now_epoch=4)
        self.assertEqual(self.q.get("verified-r1").status,"WAITING")
        self.assertEqual(self.q.get("verified-r1").payload["source"],SOURCE)
    def test_other_source_request_denied(self):
        bad={**SOURCE,"request_id":"another-request"}
        with self.assertRaisesRegex(ValueError,"source immutable"):
            self.q.requeue(request_id="verified-r1",payload={"source":bad},now_epoch=4)
        self.assertEqual(self.q.get("verified-r1").status,"WAITING")
    def test_explicit_source_null_denied(self):
        with self.assertRaisesRegex(ValueError,"source immutable"):
            self.q.requeue(request_id="verified-r1",payload={"source":None},now_epoch=4)
    def test_same_tenant_different_context_ref_denied(self):
        with self.assertRaisesRegex(ValueError,"context reference immutable"):
            self.q.requeue(request_id="verified-r1",
                payload={"context":{"console_context_ref":"channel:sales"}},now_epoch=4)
        self.assertEqual(self.q.get("verified-r1").status,"WAITING")
    def test_remove_context_ref_explicitly_denied(self):
        with self.assertRaisesRegex(ValueError,"context reference immutable"):
            self.q.requeue(request_id="verified-r1",
                payload={"context":{"console_context_ref":None}},now_epoch=4)
    def test_cross_tenant_context_remains_denied(self):
        with self.assertRaisesRegex(ValueError,"cross-company onboarding"):
            self.q.requeue(request_id="verified-r1",
                payload={"context":{"console_context_ref":"company:aion"}},now_epoch=4)
    def test_stored_scope_survives_process_restart(self):
        self.q.requeue(request_id="verified-r1",payload={"context":{"new_evidence":"receipt-1"}},now_epoch=4)
        other=OnboardingQueue(self.path)
        item=other.claim(now_epoch=5)
        self.assertEqual(item.company_id,"fenix")
        self.assertEqual(item.payload["source"],SOURCE)
        self.assertEqual(item.payload["context"]["console_context_ref"],"company:fenix")
    def test_unverified_new_source_cannot_be_injected_into_legacy_record(self):
        self.q.enqueue(request_id="legacy-r2",company_id="fenix",version="1.0.0",
            payload={"company_id":"fenix"},now_epoch=1)
        item=self.q.claim(now_epoch=4)
        self.q.complete(request_id="legacy-r2",status="WAITING",
            result={"company_id":"fenix"},now_epoch=5,claim_attempts=item.attempts)
        with self.assertRaisesRegex(ValueError,"source immutable"):
            self.q.requeue(request_id="legacy-r2",payload={"source":SOURCE},now_epoch=6)
        self.assertEqual(self.q.get("legacy-r2").status,"WAITING")
    def test_matching_source_can_redrive(self):
        self.q.requeue(request_id="verified-r1",
            payload={"source":dict(SOURCE),"context":{"classification":"updated"}},now_epoch=4)
        item=self.q.get("verified-r1")
        self.assertEqual(item.payload["source"],SOURCE)
        self.assertEqual(item.payload["context"]["classification"],"updated")
if __name__=="__main__":
    unittest.main()
