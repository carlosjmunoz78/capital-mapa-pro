import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'console'))
from onboarding_engine import OnboardingQueueEngine
from runtime.onboarding_queue import OnboardingQueue


def command(**kw):
    a={"company_id":"fenix","request_id":"req-1","environment":"LAB","version":"1.0.0","context_id":"company:fenix","user_id":"CARLOS"}
    a.update(kw);return a

def routed():return {"engine_id":"COMP-ONB-001"}

class OnboardingReplayCP74(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.queue=OnboardingQueue(Path(self.temp.name)/'queue.db');self.engine=OnboardingQueueEngine(self.queue,lambda:100)
    def tearDown(self):self.temp.cleanup()
    def test_original_request_is_idempotent(self):
        self.assertEqual(self.engine.execute(command(),routed())['decision'],'QUEUED')
        self.assertEqual(self.engine.execute(command(),routed())['decision'],'ALREADY_QUEUED')
    def test_duplicate_across_versions_is_denied(self):
        self.engine.execute(command(),routed())
        with self.assertRaises(ValueError):self.engine.execute(command(version='2.0.0'),routed())
    def test_duplicate_lab_preprod_is_denied(self):
        self.engine.execute(command(),routed())
        with self.assertRaises(ValueError):self.engine.execute(command(environment='PREPROD'),routed())
    def test_duplicate_different_user_is_denied(self):
        self.engine.execute(command(),routed())
        with self.assertRaises(ValueError):self.engine.execute(command(user_id='IMPOSTOR'),routed())
    def test_duplicate_different_context_is_denied(self):
        self.engine.execute(command(),routed())
        with self.assertRaises(ValueError):self.engine.execute(command(context_id='channel:seo'),routed())
    def test_company_context_ref_mismatch_is_denied_before_enqueue(self):
        with self.assertRaises(ValueError):self.engine.execute(command(context_id='company:aion'),routed())
        self.assertIsNone(self.queue.get('req-1'))
    def test_legacy_lab_replay_is_compatible(self):
        self.queue.enqueue(request_id='req-1',company_id='fenix',version='1.0.0',now_epoch=100,payload={
            'company_id':'fenix','version':'1.0.0','context':{'console_context_ref':'company:fenix'},
            'source':{'type':'CEREBRO_CONSOLE','user_id':'CARLOS','request_id':'req-1'},
        })
        self.assertEqual(self.engine.execute(command(),routed())['decision'],'ALREADY_QUEUED')
    def test_legacy_preprod_replay_denied(self):
        self.queue.enqueue(request_id='req-1',company_id='fenix',version='1.0.0',now_epoch=100,payload={
            'company_id':'fenix','version':'1.0.0','context':{'console_context_ref':'company:fenix'},
            'source':{'type':'CEREBRO_CONSOLE','user_id':'CARLOS','request_id':'req-1'},
        })
        with self.assertRaises(ValueError):self.engine.execute(command(environment='PREPROD'),routed())
    def test_new_record_includes_environment_for_future_replay(self):
        self.engine.execute(command(),routed())
        self.assertEqual(self.queue.get('req-1').payload['environment'],'LAB')
    def test_other_company_rejected_without_queue_mutation(self):
        self.engine.execute(command(),routed())
        with self.assertRaises(ValueError):self.engine.execute(command(company_id='aion',context_id='company:aion'),routed())
        self.assertEqual(self.queue.get('req-1').company_id,'fenix')

if __name__=='__main__':unittest.main()