import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from linkedin_prod_pipeline import LinkedInPublishRequest, LinkedInReceiptInput, validate_linkedin_publish, normalize_linkedin_receipt


class LinkedInProdPipelineTests(unittest.TestCase):
    def base(self, scenario_id):
        return dict(scenario_id=scenario_id, company_id="fenix", engine_id="linkedin", environment="PROD", version="1",
                    publication_id="pub", run_id="run", engine_enabled=True, override_authorized_once=True,
                    override_record_matches=True, idempotency_clear=True, authorized=True, content="contenido")

    def test_all_four_formats_ready_but_never_autoexecute(self):
        cases = [
            (5554207, {}),
            (9528327, {"url":"https://example.com","link_title":"x"}),
            (9522428, {"file_name":"a.jpg","file_data_present":True}),
            (9410589, {"video_name":"a.mp4","video_data_present":True}),
        ]
        for sid, extra in cases:
            data = self.base(sid); data.update(extra)
            out = validate_linkedin_publish(LinkedInPublishRequest(**data))
            self.assertEqual(out["status"], "READY_FOR_EXPLICIT_EXECUTION")
            self.assertFalse(out["external_action_allowed"])
            self.assertEqual(out["human_reason"], "SIGNATURE_REQUIRED")

    def test_missing_format_contracts_block(self):
        self.assertIn("MISSING_LINK_CONTRACT", validate_linkedin_publish(LinkedInPublishRequest(**self.base(9528327)))["blockers"])
        self.assertIn("MISSING_IMAGE_BINARY", validate_linkedin_publish(LinkedInPublishRequest(**self.base(9522428)))["blockers"])
        self.assertIn("MISSING_VIDEO_BINARY", validate_linkedin_publish(LinkedInPublishRequest(**self.base(9410589)))["blockers"])

    def test_receipt_holds_until_notion_return(self):
        out = normalize_linkedin_receipt(LinkedInReceiptInput(5554207, "fenix", "linkedin", "PROD", "1", "pub", "run", "urn:li:x", False))
        self.assertEqual(out["idempotency_status"], "LOCKED_PENDING_NOTION_RETURN")
        self.assertFalse(out["retry_publish_allowed"])
        self.assertFalse(out["external_action_allowed"])

    def test_receipt_commits_after_notion_return(self):
        out = normalize_linkedin_receipt(LinkedInReceiptInput(5554207, "fenix", "linkedin", "PROD", "1", "pub", "run", "urn:li:x", True))
        self.assertEqual(out["idempotency_status"], "COMMITTED")
        self.assertEqual(out["override_status"], "CONSUMED")
        self.assertEqual(out["platform_state"], "PUBLISHED")


if __name__ == "__main__":
    unittest.main()
