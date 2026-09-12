import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from linkedin_preflight import LinkedInPreflightRequest, plan_linkedin_preflight


class LinkedInPreflightRuntimeTests(unittest.TestCase):
    def req(self, **changes):
        data = dict(
            company_id="fenix-capital",
            engine_id="SOCIAL-PUBLISH",
            environment="LAB",
            version="1.0.0",
            publication_id="pub-1",
            run_id="run-1",
            format="texto",
            content_ready=True,
            asset_ready=True,
            url_ready=True,
            qa_passed=True,
            schedule_ready=True,
            duplicate_exists=False,
        )
        data.update(changes)
        return LinkedInPreflightRequest(**data)

    def test_native_formats_route_but_never_publish(self):
        for fmt in ("texto", "enlace", "imagen", "vídeo"):
            result = plan_linkedin_preflight(self.req(format=fmt))
            self.assertEqual(result["status"], "ROUTED_WITH_PUBLISH_ENGINE_DISABLED")
            self.assertEqual(result["preflight_status"], "PREFLIGHT_READY")
            self.assertFalse(result["external_action_allowed"])
            self.assertEqual(result["platform_state"], "LINKEDIN_NOT_CALLED")

    def test_format_specific_gates_match_old_contract(self):
        self.assertEqual(plan_linkedin_preflight(self.req(format="enlace", url_ready=False))["status"], "BLOCKED_PREFLIGHT")
        self.assertEqual(plan_linkedin_preflight(self.req(format="imagen", asset_ready=False))["status"], "BLOCKED_PREFLIGHT")
        self.assertEqual(plan_linkedin_preflight(self.req(format="vídeo", asset_ready=False))["status"], "BLOCKED_PREFLIGHT")
        self.assertEqual(plan_linkedin_preflight(self.req(format="texto", asset_ready=False, url_ready=False))["status"], "ROUTED_WITH_PUBLISH_ENGINE_DISABLED")

    def test_duplicate_is_fail_closed(self):
        result = plan_linkedin_preflight(self.req(duplicate_exists=True))
        self.assertEqual(result["status"], "BLOCKED_DUPLICATE")
        self.assertFalse(result["external_action_allowed"])

    def test_document_and_carousel_require_adapter(self):
        for fmt in ("documento", "carrusel"):
            result = plan_linkedin_preflight(self.req(format=fmt))
            self.assertEqual(result["status"], "ADAPTER_REQUIRED")
            self.assertTrue(result["adapter_required"])
            self.assertFalse(result["external_action_allowed"])

    def test_scope_and_environment_are_explicit(self):
        result = plan_linkedin_preflight(self.req(environment="PROD"))
        self.assertEqual(result["company_id"], "fenix-capital")
        self.assertEqual(result["engine_id"], "SOCIAL-PUBLISH")
        self.assertEqual(result["environment"], "PROD")
        self.assertEqual(result["version"], "1.0.0")
        with self.assertRaises(ValueError):
            plan_linkedin_preflight(self.req(environment="DEV"))


if __name__ == "__main__":
    unittest.main()
