import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from runtime.onboarding_queue import OnboardingQueue
from runtime.onboarding_worker_service import WorkerServicePolicy,run_service_cycles

class OnboardingWorkerServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.queue=OnboardingQueue(Path(self.tmp.name)/"queue.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def test_empty_service_cycles_sleep_without_busy_loop_and_write_heartbeat(self):
        clock={"now":100}
        sleeps=[]
        def now():
            return clock["now"]
        def sleep(seconds):
            sleeps.append(seconds)
            clock["now"]+=seconds
        heartbeat=Path(self.tmp.name)/"heartbeat.json"
        out=run_service_cycles(
            queue=self.queue,now_epoch_provider=now,sleep=sleep,
            policy=WorkerServicePolicy(min_sleep_seconds=5,max_idle_sleep_seconds=60),
            max_cycles=3,heartbeat_path=heartbeat,
        )
        self.assertEqual(out["cycle_count"],3)
        self.assertEqual(sleeps,[60,60])
        self.assertTrue(out["continuous_mode_supported"])
        self.assertTrue(heartbeat.exists())
        row=json.loads(heartbeat.read_text())
        self.assertEqual(row["engine_id"],"ONB-SVC-HLT-001")
        self.assertEqual(row["processed_count"],0)
        self.assertFalse(row["external_mutation_allowed"])

    def test_service_sleeps_until_scheduled_retry_when_sooner_than_idle_cap(self):
        self.queue.enqueue(
            request_id="r1",company_id="fenix",version="1.0.0",
            payload={"company_id":"fenix","version":"1.0.0","context":{}},now_epoch=100,
        )
        self.queue.claim(now_epoch=110,lease_seconds=30)
        self.queue.retry_or_dead_letter(
            request_id="r1",
            result={"company_id":"fenix","status":"BLOCKED","reason":"EXECUTOR_EXCEPTION"},
            now_epoch=110,max_attempts=3,base_backoff_seconds=40,max_backoff_seconds=600,
        )
        clock={"now":120}
        sleeps=[]
        def now():
            return clock["now"]
        def sleep(seconds):
            sleeps.append(seconds)
            clock["now"]+=seconds
        dummy={
          "status":"GREEN","processed_count":0,"items":(),"queue_stats":self.queue.stats(now_epoch=120),
          "human_required_count":0,"blocked_count":0,"retry_scheduled_count":0,
          "external_mutation_allowed":False,"production_activation_allowed":False,"cost_eur":0.0,
        }
        with patch("runtime.onboarding_worker_service.process_batch",return_value=dummy):
            run_service_cycles(
                queue=self.queue,now_epoch_provider=now,sleep=sleep,
                policy=WorkerServicePolicy(min_sleep_seconds=5,max_idle_sleep_seconds=60),
                max_cycles=2,
            )
        self.assertEqual(sleeps,[30])

    def test_service_never_claims_dead_letter_without_explicit_requeue(self):
        self.queue.enqueue(
            request_id="r1",company_id="fenix",version="1.0.0",
            payload={"company_id":"fenix","version":"1.0.0","context":{}},now_epoch=100,
        )
        self.queue.claim(now_epoch=110,lease_seconds=30)
        self.queue.retry_or_dead_letter(
            request_id="r1",
            result={"company_id":"fenix","status":"BLOCKED","reason":"EXECUTOR_EXCEPTION"},
            now_epoch=111,max_attempts=1,base_backoff_seconds=60,max_backoff_seconds=600,
        )
        out=run_service_cycles(
            queue=self.queue,now_epoch_provider=lambda:200,sleep=lambda _:None,
            max_cycles=1,
        )
        self.assertEqual(out["cycles"][0]["processed_count"],0)
        self.assertEqual(self.queue.get("r1").status,"DEAD_LETTER")

    def test_invalid_policy_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"sleep policy"):
            WorkerServicePolicy(min_sleep_seconds=60,max_idle_sleep_seconds=10).validate()

if __name__=="__main__":
    unittest.main()
