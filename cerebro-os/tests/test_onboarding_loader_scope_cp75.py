import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"console"))
from onboarding_engine import OnboardingQueueEngine
from runtime.onboarding_queue import OnboardingQueue

def command(**overrides):
    row={"company_id":"fenix","request_id":"cp75-one","environment":"LAB",
         "version":"1.0.0","context_id":"company:fenix","user_id":"CARLOS"}
    row.update(overrides)
    return row

def routed():
    return {"engine_id":"COMP-ONB-001"}

class OnboardingLoaderScopeCP75(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.queue=OnboardingQueue(Path(self.tmp.name)/"queue.sqlite3")
    def tearDown(self):
        self.tmp.cleanup()
    def engine(self,loader):
        return OnboardingQueueEngine(self.queue,lambda:100,context_loader=loader)

    def test_loader_cross_company_ref_cannot_override_valid_input(self):
        e=self.engine(lambda company,ctx,cmd:{"company_id":company,"console_context_ref":"company:aion"})
        with self.assertRaisesRegex(ValueError,"cross-company loaded"):
            e.execute(command(),routed())
        self.assertIsNone(self.queue.get("cp75-one"))

    def test_loader_cross_company_ref_without_input_is_denied(self):
        e=self.engine(lambda company,ctx,cmd:{"console_context_ref":"company:aion"})
        with self.assertRaisesRegex(ValueError,"cross-company loaded"):
            e.execute(command(context_id=""),routed())
        self.assertIsNone(self.queue.get("cp75-one"))

    def test_loader_different_context_ref_cannot_replace_user_request(self):
        e=self.engine(lambda company,ctx,cmd:{"console_context_ref":"channel:seo"})
        with self.assertRaisesRegex(ValueError,"reference mismatch"):
            e.execute(command(),routed())
        self.assertIsNone(self.queue.get("cp75-one"))

    def test_loader_empty_context_ref_denied(self):
        e=self.engine(lambda company,ctx,cmd:{"console_context_ref":""})
        with self.assertRaisesRegex(ValueError,"invalid loaded"):
            e.execute(command(),routed())
        self.assertIsNone(self.queue.get("cp75-one"))

    def test_loader_non_string_context_ref_denied(self):
        e=self.engine(lambda company,ctx,cmd:{"console_context_ref":{"company_id":"aion"}})
        with self.assertRaisesRegex(ValueError,"invalid loaded"):
            e.execute(command(),routed())
        self.assertIsNone(self.queue.get("cp75-one"))

    def test_same_company_loader_reference_and_extra_metadata_preserved(self):
        e=self.engine(lambda company,ctx,cmd:{"company_id":company,"console_context_ref":"company:fenix","profile":"mortgage"})
        result=e.execute(command(),routed())
        self.assertEqual(result["decision"],"QUEUED")
        q=self.queue.get("cp75-one")
        self.assertEqual(q.payload["context"]["console_context_ref"],"company:fenix")
        self.assertEqual(q.payload["context"]["profile"],"mortgage")
        self.assertEqual(e.execute(command(),routed())["decision"],"ALREADY_QUEUED")

    def test_compatible_loader_without_reference_preserved(self):
        e=self.engine(lambda company,ctx,cmd:{"company_id":"fenix","authorized":True})
        self.assertEqual(e.execute(command(),routed())["decision"],"QUEUED")
        self.assertEqual(self.queue.get("cp75-one").payload["context"]["authorized"],True)

    def test_loader_cross_company_field_still_denied(self):
        e=self.engine(lambda company,ctx,cmd:{"company_id":"aion","authorized":True})
        with self.assertRaisesRegex(ValueError,"cross-company onboarding context"):
            e.execute(command(),routed())
        self.assertIsNone(self.queue.get("cp75-one"))

    def test_invalid_loader_reference_does_not_modify_existing_job(self):
        good=self.engine(lambda company,ctx,cmd:{"console_context_ref":"company:fenix"})
        good.execute(command(),routed())
        bad=self.engine(lambda company,ctx,cmd:{"console_context_ref":"company:aion"})
        with self.assertRaisesRegex(ValueError,"cross-company loaded"):
            bad.execute(command(),routed())
        self.assertEqual(self.queue.get("cp75-one").payload["context"]["console_context_ref"],"company:fenix")

if __name__=="__main__":
    unittest.main()
