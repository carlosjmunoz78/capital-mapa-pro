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

    def test_console_audit_and_history_persist_across_runtime_restart(self):
        queue_path=Path(self.tmp.name)/"persistent-queue.sqlite3"
        first=build_console_runtime(
            queue_path=queue_path,
            now_epoch_provider=lambda:123,
            company_reader=lambda:({"company_id":"fenix","name":"Fenix","status":"ACTIVE"},),
        )
        response=first.surface.handle(
            method="POST",path="/commands",user_id="CARLOS",
            payload={
              "request_id":"req-persist","company_id":"fenix","context_type":"company",
              "message":"crear empresa","environment":"LAB","version":"1.0.0",
            },
        )
        self.assertEqual(response.status,200)
        self.assertEqual(first.store.counts(),{"audit":1,"history":1})

        second=build_console_runtime(
            queue_path=queue_path,
            now_epoch_provider=lambda:200,
            company_reader=lambda:({"company_id":"fenix","name":"Fenix","status":"ACTIVE"},),
        )
        history=second.surface.handle(method="GET",path="/history/fenix",user_id="CARLOS")
        audit=second.surface.handle(method="GET",path="/audit/fenix",user_id="CARLOS")
        self.assertEqual(history.status,200)
        self.assertEqual(audit.status,200)
        self.assertEqual(history.body["items"][0]["request_id"],"req-persist")
        self.assertEqual(history.body["items"][0]["engine_id"],"COMP-ONB-001")
        self.assertEqual(audit.body["items"][0]["result"],"WAITING")
        self.assertEqual(audit.body["items"][0]["action"],"CREATE_COMPANY")
        self.assertEqual(audit.body["items"][0]["timestamp"],"123")


    def test_company_onboarding_status_endpoint_exposes_safe_queue_state(self):
        self.runtime.surface.handle(
            method="POST",path="/commands",user_id="CARLOS",
            payload={
              "request_id":"req-status","company_id":"fenix","context_type":"company",
              "message":"crear empresa","environment":"LAB","version":"1.0.0",
            },
        )
        queued=self.runtime.surface.handle(
            method="GET",path="/onboarding/company/fenix",user_id="CARLOS"
        )
        self.assertEqual(queued.status,200)
        self.assertEqual(queued.body["items"][0]["request_id"],"req-status")
        self.assertEqual(queued.body["items"][0]["status"],"QUEUED")
        self.assertNotIn("payload",queued.body["items"][0])

        self.runtime.queue.complete(
            request_id="req-status",status="WAITING",now_epoch=120,
            result={
              "company_id":"fenix","status":"WAITING","stop_reason":"ENGINE_NOT_GREEN",
              "state":{"current_phase":"MINIMUM_ACCESSES"},
              "remote_prefill":{"green_engine_count":7},
              "external_mutation_allowed":False,"production_activation_allowed":False,"cost_eur":0.0,
            },
        )
        waiting=self.runtime.surface.handle(
            method="GET",path="/onboarding/company/fenix",user_id="CARLOS"
        )
        row=waiting.body["items"][0]
        self.assertEqual(row["status"],"WAITING")
        self.assertEqual(row["current_phase"],"MINIMUM_ACCESSES")
        self.assertEqual(row["stop_reason"],"ENGINE_NOT_GREEN")
        self.assertEqual(row["remote_prefill_green"],7)
        self.assertEqual(self.runtime.surface.handle(
            method="GET",path="/onboarding/company/aion",user_id="CARLOS"
        ).body["items"],())


    def test_remote_gap_endpoint_reports_what_can_continue_without_local_pc(self):
        queue_path=Path(self.tmp.name)/"remote-gap-queue.sqlite3"
        runtime=build_console_runtime(
            queue_path=queue_path,
            now_epoch_provider=lambda:100,
            company_reader=lambda:({"company_id":"fenix","name":"Fenix","status":"ACTIVE"},),
        )
        runtime.queue.enqueue(
            request_id="req-gap",company_id="fenix",version="1.0.0",now_epoch=100,
            payload={"company_id":"fenix","version":"1.0.0"},
        )
        runtime.queue.complete(
            request_id="req-gap",status="WAITING",now_epoch=101,
            result={
              "company_id":"fenix","version":"1.0.0","status":"WAITING",
              "state":{"company_id":"fenix","environment":"LAB","current_phase":"SCAN_DIGITAL_FOOTPRINT"},
              "remote_prefill":{"engine_count":13,"green_engine_count":5},
              "executor_stop_reason":"ENGINE_RESULT_MISSING",
            },
        )
        response=runtime.surface.handle(method="GET",path="/onboarding/remote/fenix",user_id="CARLOS")
        self.assertEqual(response.status,200)
        row=response.body["items"][0]
        self.assertEqual(row["classification"],"REMOTE_SAFE")
        self.assertTrue(row["remotely_actionable"])
        self.assertFalse(row["local_pc_required"])
        self.assertEqual(row["remote_prefill_remaining"],8)


    def test_console_onboarding_can_load_remote_safe_company_context(self):
        queue_path=Path(self.tmp.name)/"context-loader-queue.sqlite3"
        seen=[]
        def loader(company_id,context_id,command):
            seen.append((company_id,context_id,command["request_id"]))
            return {
              "company_id":"fenix",
              "company_profile":{"legal_name":"Fenix Test","evidence_ref":"doc://company"},
              "access_requirements":[{"capability":"crm","purpose":"sales","provider":"existing","required":True}],
              "existing_accounts":[],"existing_connectors":[],"session_observations":[],"domains":[],
            }
        runtime=build_console_runtime(
            queue_path=queue_path,
            now_epoch_provider=lambda:100,
            onboarding_context_loader=loader,
            company_reader=lambda:({"company_id":"fenix","name":"Fenix","status":"ACTIVE"},),
        )
        response=runtime.surface.handle(
            method="POST",path="/commands",user_id="CARLOS",
            payload={
              "request_id":"req-context","company_id":"fenix","context_type":"company","context_id":"company:fenix",
              "message":"crear empresa","environment":"LAB","version":"1.0.0",
            },
        )
        self.assertEqual(response.status,200)
        item=runtime.queue.get("req-context")
        self.assertEqual(item.payload["context"]["company_profile"]["legal_name"],"Fenix Test")
        self.assertEqual(item.payload["context"]["console_context_ref"],"company:fenix")
        self.assertEqual(seen,[("fenix","company:fenix","req-context")])

    def test_console_onboarding_context_loader_denies_cross_company_context(self):
        runtime=build_console_runtime(
            queue_path=Path(self.tmp.name)/"cross-context.sqlite3",
            now_epoch_provider=lambda:100,
            onboarding_context_loader=lambda company_id,context_id,command:{"company_id":"aion"},
        )
        response=runtime.surface.handle(
            method="POST",path="/commands",user_id="CARLOS",
            payload={
              "request_id":"req-cross","company_id":"fenix","context_type":"company",
              "message":"crear empresa","environment":"LAB","version":"1.0.0",
            },
        )
        self.assertEqual(response.status,400)
        self.assertEqual(response.body["error"],"invalid_command")
        self.assertIsNone(runtime.queue.get("req-cross"))

    def test_console_onboarding_context_loader_raw_secret_is_rejected_by_queue(self):
        runtime=build_console_runtime(
            queue_path=Path(self.tmp.name)/"secret-context.sqlite3",
            now_epoch_provider=lambda:100,
            onboarding_context_loader=lambda company_id,context_id,command:{"password":"never-store"},
        )
        response=runtime.surface.handle(
            method="POST",path="/commands",user_id="CARLOS",
            payload={
              "request_id":"req-secret","company_id":"fenix","context_type":"company",
              "message":"crear empresa","environment":"LAB","version":"1.0.0",
            },
        )
        self.assertEqual(response.status,400)
        self.assertIsNone(runtime.queue.get("req-secret"))


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
