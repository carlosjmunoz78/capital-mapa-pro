import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from runtime.onboarding_queue import OnboardingQueue
from jobs.run_company_onboarding_worker import process_batch
from jobs.build_onboarding_worker_health import evaluate_worker_health

class OnboardingWorkerSupervisorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.queue=OnboardingQueue(Path(self.tmp.name)/"queue.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def _payload(self,company_id):
        return {
          "company_id":company_id,"version":"1.0.0","max_steps":5,
          "context":{
            "company_profile":{"legal_name":company_id.title(),"evidence_ref":f"doc://{company_id}"},
            "access_requirements":[],"existing_accounts":[],"existing_connectors":[],
            "session_observations":[],"domains":[],
          }
        }

    def test_batch_processes_multiple_companies_without_manual_ok(self):
        self.queue.enqueue(request_id="r1",company_id="fenix",version="1.0.0",payload=self._payload("fenix"),now_epoch=100)
        self.queue.enqueue(request_id="r2",company_id="aion",version="1.0.0",payload=self._payload("aion"),now_epoch=101)
        out=process_batch(queue=self.queue,now_epoch=110,max_items=10,lease_seconds=30)
        self.assertEqual(out["processed_count"],2)
        self.assertEqual(out["status"],"GREEN")
        self.assertEqual(out["queue_stats"]["waiting"],2)
        self.assertFalse(out["external_mutation_allowed"])

    def test_batch_honors_max_items(self):
        for i,cid in enumerate(("a","b","c"),1):
            self.queue.enqueue(request_id=f"r{i}",company_id=cid,version="1.0.0",payload=self._payload(cid),now_epoch=100+i)
        out=process_batch(queue=self.queue,now_epoch=120,max_items=2)
        self.assertEqual(out["processed_count"],2)
        self.assertEqual(out["queue_stats"]["queued"],1)

    def test_health_detects_stale_lease(self):
        self.queue.enqueue(request_id="r1",company_id="fenix",version="1.0.0",payload=self._payload("fenix"),now_epoch=100)
        self.queue.claim(now_epoch=110,lease_seconds=5)
        health=evaluate_worker_health(queue=self.queue,now_epoch=116)
        self.assertEqual(health["status"],"DEGRADED")
        self.assertEqual(health["queue_stats"]["stale_leases"],1)
        self.assertTrue(health["stale_lease_reclaim_supported"])

    def test_health_is_green_for_empty_or_waiting_queue_without_failures(self):
        empty=evaluate_worker_health(queue=self.queue,now_epoch=100)
        self.assertEqual(empty["status"],"GREEN")
        self.queue.enqueue(request_id="r1",company_id="fenix",version="1.0.0",payload=self._payload("fenix"),now_epoch=100)
        process_batch(queue=self.queue,now_epoch=110,max_items=1)
        waiting=evaluate_worker_health(queue=self.queue,now_epoch=120)
        self.assertEqual(waiting["status"],"GREEN")

    def test_health_degrades_when_retry_is_scheduled(self):
        self.queue.enqueue(request_id="r1",company_id="fenix",version="1.0.0",payload=self._payload("fenix"),now_epoch=100)
        self.queue.claim(now_epoch=110,lease_seconds=5)
        self.queue.retry_or_dead_letter(
            request_id="r1",
            result={"company_id":"fenix","status":"BLOCKED","reason":"EXECUTOR_EXCEPTION"},
            now_epoch=111,max_attempts=3,base_backoff_seconds=60,max_backoff_seconds=600,
        )
        health=evaluate_worker_health(queue=self.queue,now_epoch=120)
        self.assertEqual(health["status"],"DEGRADED")
        self.assertEqual(health["queue_stats"]["retry_scheduled"],1)
        self.assertTrue(health["retry_backoff_supported"])
        self.assertTrue(health["dead_letter_supported"])
        self.assertTrue(health["priority_queue_supported"])

    def test_health_degrades_when_dead_letter_exists(self):
        self.queue.enqueue(request_id="r1",company_id="fenix",version="1.0.0",payload=self._payload("fenix"),now_epoch=100)
        self.queue.claim(now_epoch=110,lease_seconds=5)
        self.queue.retry_or_dead_letter(
            request_id="r1",
            result={"company_id":"fenix","status":"BLOCKED","reason":"EXECUTOR_EXCEPTION"},
            now_epoch=111,max_attempts=1,base_backoff_seconds=60,max_backoff_seconds=600,
        )
        health=evaluate_worker_health(queue=self.queue,now_epoch=120)
        self.assertEqual(health["status"],"DEGRADED")
        self.assertEqual(health["queue_stats"]["dead_letter"],1)


if __name__=="__main__":
    unittest.main()
