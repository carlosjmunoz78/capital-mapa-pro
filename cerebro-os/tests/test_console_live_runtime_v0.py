import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"console"))

from runtime_builder import build_console_runtime
from http_surface import wsgi_app

class ConsoleLiveRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.runtime=build_console_runtime(
            queue_path=Path(self.tmp.name)/"queue.sqlite3",
            now_epoch_provider=lambda:100,
            company_reader=lambda:({"company_id":"fenix","name":"Fenix","status":"ACTIVE"},),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_console_command_crear_empresa_reaches_real_onboarding_queue(self):
        response=self.runtime.surface.handle(
            method="POST",path="/commands",user_id="CARLOS",
            payload={
              "request_id":"req-1","company_id":"fenix","context_type":"company","context_id":"company:fenix",
              "message":"crear empresa","environment":"LAB","version":"1.0.0",
            },
        )
        self.assertEqual(response.status,200)
        self.assertEqual(response.body["result"]["execution_mode"],"EXECUTED")
        self.assertEqual(response.body["result"]["engine_result"]["decision"],"QUEUED")
        item=self.runtime.queue.get("req-1")
        self.assertIsNotNone(item)
        self.assertEqual(item.company_id,"fenix")
        self.assertEqual(len(self.runtime.audits),1)

    def test_unknown_console_command_never_executes_or_queues(self):
        response=self.runtime.surface.handle(
            method="POST",path="/commands",user_id="CARLOS",
            payload={
              "request_id":"req-x","company_id":"fenix","context_type":"company",
              "message":"haz algo desconocido","environment":"LAB","version":"1.0.0",
            },
        )
        self.assertEqual(response.body["result"]["status"],"HUMAN_REQUIRED")
        self.assertEqual(response.body["result"]["execution_mode"],"ROUTE_ONLY")
        self.assertIsNone(self.runtime.queue.get("req-x"))

    def test_onboarding_queue_health_endpoint_uses_live_queue(self):
        self.runtime.surface.handle(
            method="POST",path="/commands",user_id="CARLOS",
            payload={
              "request_id":"req-1","company_id":"fenix","context_type":"company",
              "message":"crear empresa","environment":"LAB","version":"1.0.0",
            },
        )
        response=self.runtime.surface.handle(method="GET",path="/onboarding/queue",user_id="CARLOS")
        self.assertEqual(response.status,200)
        self.assertEqual(response.body["onboarding"]["queue_stats"]["queued"],1)
        self.assertTrue(response.body["onboarding"]["worker_autonomous"])

    def test_wsgi_requires_trusted_identity_and_can_queue_when_remote_user_exists(self):
        app=wsgi_app(self.runtime.surface)
        calls=[]
        def start_response(status,headers):
            calls.append((status,dict(headers)))
        payload=json.dumps({
          "request_id":"req-wsgi","company_id":"fenix","context_type":"company",
          "message":"crear empresa","environment":"LAB","version":"1.0.0"
        }).encode()
        body=b"".join(app({
          "REQUEST_METHOD":"POST","PATH_INFO":"/commands","REMOTE_USER":"CARLOS",
          "CONTENT_LENGTH":str(len(payload)),"wsgi.input":io.BytesIO(payload),
        },start_response))
        self.assertTrue(calls[0][0].startswith("200"))
        decoded=json.loads(body)
        self.assertEqual(decoded["result"]["engine_result"]["decision"],"QUEUED")
        self.assertIsNotNone(self.runtime.queue.get("req-wsgi"))

if __name__=="__main__":
    unittest.main()
