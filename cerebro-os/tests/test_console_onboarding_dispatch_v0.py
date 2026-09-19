import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"console"))
sys.path.insert(0,str(ROOT))

from pipeline import ConsolePipeline
from engine_dispatch import EngineDispatcher
from onboarding_engine import OnboardingQueueEngine
from runtime.onboarding_queue import OnboardingQueue

class ConsoleOnboardingDispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.queue=OnboardingQueue(Path(self.tmp.name)/"queue.sqlite3")
        self.dispatcher=EngineDispatcher()
        self.onboarding=OnboardingQueueEngine(self.queue,lambda:100)
        self.dispatcher.register("COMP-ONB-001",self.onboarding.execute)
        self.audits=[]

    def tearDown(self):
        self.tmp.cleanup()

    def _gateway(self,command):
        return {
          "status":"ROUTED","company_id":command["company_id"],"environment":command["environment"],
          "version":command["version"],"engine_id":"COMP-ONB-001"
        }

    def _command(self,**overrides):
        row={
          "request_id":"req-1","user_id":"CARLOS","company_id":"fenix","context_type":"company",
          "context_id":"company:fenix","message":"crear empresa","environment":"LAB","version":"1.0.0"
        }
        row.update(overrides); return row

    def test_console_route_executes_comp_onb_and_enqueues_request(self):
        pipe=ConsolePipeline(self._gateway,self.audits.append,self.dispatcher.execute)
        out=pipe.execute(self._command())
        self.assertEqual(out["execution_mode"],"EXECUTED")
        self.assertEqual(out["status"],"WAITING")
        self.assertEqual(out["engine_result"]["decision"],"QUEUED")
        queued=self.queue.get("req-1")
        self.assertIsNotNone(queued)
        self.assertEqual(queued.company_id,"fenix")
        self.assertEqual(queued.payload["context"]["console_context_ref"],"company:fenix")
        self.assertEqual(self.audits[0]["engine_status"],"WAITING")

    def test_duplicate_console_request_is_idempotent(self):
        pipe=ConsolePipeline(self._gateway,self.audits.append,self.dispatcher.execute)
        first=pipe.execute(self._command())
        second=pipe.execute(self._command())
        self.assertEqual(first["engine_result"]["decision"],"QUEUED")
        self.assertEqual(second["engine_result"]["decision"],"ALREADY_QUEUED")
        self.assertEqual(self.queue.get("req-1").attempts,0)

    def test_prod_submission_is_high_risk_and_not_queued(self):
        pipe=ConsolePipeline(self._gateway,self.audits.append,self.dispatcher.execute)
        out=pipe.execute(self._command(environment="PROD"))
        self.assertEqual(out["status"],"HUMAN_REQUIRED")
        self.assertEqual(out["engine_result"]["human_reason"],"HIGH_RISK")
        self.assertFalse(out["engine_result"]["queued"])
        self.assertIsNone(self.queue.get("req-1"))

    def test_unregistered_engine_fails_closed(self):
        dispatcher=EngineDispatcher()
        routed={"status":"ROUTED","company_id":"fenix","environment":"LAB","version":"1.0.0","engine_id":"UNKNOWN-001"}
        out=dispatcher.execute(self._command(),routed)
        self.assertEqual(out["status"],"BLOCKED")
        self.assertEqual(out["reason"],"ENGINE_HANDLER_NOT_REGISTERED")

if __name__=="__main__":
    unittest.main()
