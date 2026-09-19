import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "console"
sys.path.insert(0, str(CONSOLE))

from http_surface import ConsoleHttpSurface, wsgi_app
from pipeline import ConsolePipeline


class ConsoleHttpSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.audit = []

        def gateway(command):
            return {
                "status": "ROUTED",
                "company_id": command["company_id"],
                "environment": command["environment"],
                "version": command["version"],
                "engine_id": "ENG-001",
            }

        self.surface = ConsoleHttpSurface(
            ConsolePipeline(gateway, self.audit.append),
            lambda: ({"company_id": "FENIX", "name": "Fenix Capital", "status": "ACTIVE", "secret": "never"},),
            context_reader=lambda company_id: ({"company_id": company_id, "context_type": "company", "context_id": company_id, "label": "Empresa", "status": "ACTIVE", "secret": "never"},),
            engine_reader=lambda company_id: ({"company_id": company_id, "engine_id": "ENG-001", "name": "Engine", "status": "GREEN", "environment": "LAB", "version": "1.0.0", "secret": "never"},),
            history_reader=lambda company_id: ({"company_id": company_id, "request_id": "REQ-H1", "engine_id": "ENG-001", "status": "GREEN", "evidence_ref": "e://1", "environment": "LAB", "version": "1.0.0", "secret": "never"},),
            audit_reader=lambda company_id: ({"company_id": company_id, "request_id": "REQ-A1", "engine_id": "ENG-001", "action": "STATUS", "result": "GREEN", "evidence_ref": "e://a", "timestamp": "2026-09-19T22:00:00Z", "secret": "never"},),
        )

    def test_health_proves_no_direct_model_path(self):
        r = self.surface.handle(method="GET", path="/health", user_id="CARLOS")
        self.assertEqual(r.status, 200)
        self.assertFalse(r.body["direct_model"])
        self.assertEqual(r.headers["x-cerebro-gateway"], "required")

    def test_company_selector_does_not_expose_unapproved_fields(self):
        r = self.surface.handle(method="GET", path="/companies", user_id="CARLOS")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.body["items"], ({"company_id": "FENIX", "name": "Fenix Capital", "status": "ACTIVE"},))
        self.assertNotIn("secret", r.body["items"][0])

    def test_command_can_only_execute_through_pipeline_and_is_audited(self):
        r = self.surface.handle(
            method="POST",
            path="/commands",
            user_id="CARLOS",
            payload={
                "request_id": "REQ-1",
                "company_id": "FENIX",
                "context_type": "company",
                "message": "estado",
                "environment": "LAB",
                "version": "1.0.0",
            },
        )
        self.assertEqual(r.status, 200)
        self.assertEqual(r.body["result"]["path"], ("CONSOLE", "GATEWAY", "POLICY", "ENGINE", "AUDIT"))
        self.assertEqual(len(self.audit), 1)
        self.assertEqual(self.audit[0]["company_id"], "FENIX")

    def test_console_v0_exposes_context_engine_history_and_audit_scoped_to_company(self):
        cases = {
            "/contexts/FENIX": ("context_type", "secret"),
            "/engines/FENIX": ("engine_id", "secret"),
            "/history/FENIX": ("request_id", "secret"),
            "/audit/FENIX": ("action", "secret"),
        }
        for path, (expected, forbidden) in cases.items():
            r = self.surface.handle(method="GET", path=path, user_id="CARLOS")
            self.assertEqual(r.status, 200)
            self.assertEqual(r.body["company_id"], "FENIX")
            self.assertEqual(len(r.body["items"]), 1)
            self.assertIn(expected, r.body["items"][0])
            self.assertNotIn(forbidden, r.body["items"][0])

    def test_scoped_console_route_requires_company_id(self):
        r = self.surface.handle(method="GET", path="/contexts/", user_id="CARLOS")
        self.assertEqual(r.status, 400)
        self.assertEqual(r.body["error"], "company_id_required")

    def test_identity_is_not_accepted_from_json(self):
        calls = []

        def start_response(status, headers):
            calls.append((status, dict(headers)))

        app = wsgi_app(self.surface)
        payload = json.dumps({"user_id": "IMPOSTOR", "company_id": "FENIX"}).encode()
        body = b"".join(app({
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/commands",
            "HTTP_X_CEREBRO_USER_ID": "",
            "CONTENT_LENGTH": str(len(payload)),
            "wsgi.input": io.BytesIO(payload),
        }, start_response))
        self.assertTrue(calls[0][0].startswith("401"))
        self.assertEqual(json.loads(body)["error"], "unauthorized")


if __name__ == "__main__":
    unittest.main()
