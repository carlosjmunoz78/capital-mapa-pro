import base64
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "cerebro-os" / "factory"
def load(path, name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

factory=load("factory.py","factory_for_enrollment_test")
enroll=load("universal_media_enrollment.py","enrollment_test")

class FakeResponse:
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self): return b'{"success":true,"result":{}}'

class EnrollmentTests(unittest.TestCase):
    def test_scaffold_auto_inherits_and_emits_outbox(self):
        with tempfile.TemporaryDirectory() as td:
            target=factory.scaffold(Path(td),"FACT-TEST-071","Factory test",company_id="fenix")
            result=json.loads((target/"events"/"UMS001_FACTORY_ENROLLMENT_STATUS.json").read_text())
            self.assertEqual(result["status"],"PENDING_FACTORY_IAM_TRANSPORT")
            event=json.loads((target/"events"/"FACT001_ENGINE_CREATED.outbox.json").read_text())
            self.assertEqual(event["event_type"],"FACT001_ENGINE_CREATED")
            self.assertEqual(event["engine_id"],"FACT-TEST-071")
            self.assertEqual(event["company_id"],"fenix")
            self.assertFalse(result["media_dispatch_enabled"])

    def test_missing_company_is_not_authed(self):
        with tempfile.TemporaryDirectory() as td:
            target=factory.scaffold(Path(td),"FACT-TEST-072","Factory test")
            result=json.loads((target/"events"/"UMS001_FACTORY_ENROLLMENT_STATUS.json").read_text())
            self.assertEqual(result["status"],"PENDING_COMPANY_IAM")
            self.assertFalse((target/"events"/"FACT001_ENGINE_CREATED.outbox.json").exists())

    def test_signed_dispatch_uses_single_queue_and_no_secret_leak(self):
        with tempfile.TemporaryDirectory() as td:
            target=factory.scaffold(Path(td),"FACT-TEST-073","Factory test")
            captured=[]
            def transport(req,timeout):
                self.assertEqual(timeout,8)
                captured.append(req)
                return FakeResponse()
            env={"CEREBRO_FACT_ENROLL_EVENT_KEY":"x"*64,
                 "CEREBRO_CLOUDFLARE_API_TOKEN":"test-api-secret",
                 "CEREBRO_CLOUDFLARE_ACCOUNT_ID":"a"*32,
                 "CEREBRO_FACT_ENROLL_QUEUE_ID":"b"*32}
            status=enroll.enroll_factory_engine(
                target,factory.build_manifest("FACT-TEST-073","Test"),
                company_id="fenix",environ=env,transport=transport)
            self.assertEqual(status["status"],"QUEUED_SIGNED_ENROLLMENT_PENDING_GATEWAY_ACK")
            self.assertEqual(len(captured),1)
            payload=json.loads(captured[0].data)["body"]
            self.assertEqual(len(base64.b64decode(payload["signature"])),32)
            self.assertNotIn("test-api-secret",(target/"events"/"UMS001_FACTORY_ENROLLMENT_STATUS.json").read_text())
            self.assertEqual(payload["event_type"],"FACT001_ENGINE_CREATED")

    def test_cross_company_deny_and_no_publication(self):
        with tempfile.TemporaryDirectory() as td:
            target=factory.scaffold(Path(td),"FACT-TEST-074","Factory test",company_id="other-company")
            result=json.loads((target/"events"/"UMS001_FACTORY_ENROLLMENT_STATUS.json").read_text())
            self.assertEqual(result["status"],"HOLD_INVALID_FACTORY_SCOPE")
            media=json.loads((target/"config"/"ums001_universal_media.json").read_text())
            self.assertFalse(media["security"]["publish_authorized"])

if __name__=="__main__": unittest.main()
