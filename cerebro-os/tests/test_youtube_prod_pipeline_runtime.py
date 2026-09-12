import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from youtube_prod_pipeline import YouTubeUploadRequest, validate_youtube_upload


class YouTubeProdPipelineTests(unittest.TestCase):
    def base(self, scenario_id, fmt):
        return dict(scenario_id=scenario_id, company_id="fenix", engine_id="youtube", environment="PROD", version="1",
                    publication_id="pub", run_id="run", engine_enabled=True, override_authorized_once=True,
                    override_record_matches=True, idempotency_clear=True, authorized=True, format=fmt,
                    title="title", description="description", file_name="video.mp4", video_data_present=True,
                    duration_seconds=60 if fmt == "SHORT" else 300, qa_passed=True,
                    vertical_validated=(fmt == "SHORT"), horizontal_validated=(fmt == "LONG_VIDEO"))

    def test_short_contract(self):
        out = validate_youtube_upload(YouTubeUploadRequest(**self.base(9537699, "SHORT")))
        self.assertEqual(out["status"], "READY_FOR_EXPLICIT_EXECUTION")
        self.assertEqual(out["privacy_status"], "private")
        self.assertFalse(out["external_action_allowed"])
        self.assertFalse(out["retry_upload_allowed"])
        self.assertEqual(out["human_reason"], "SIGNATURE_REQUIRED")

    def test_long_contract(self):
        out = validate_youtube_upload(YouTubeUploadRequest(**self.base(9537702, "LONG_VIDEO")))
        self.assertEqual(out["status"], "READY_FOR_EXPLICIT_EXECUTION")
        self.assertEqual(out["privacy_status"], "private")

    def test_boundary_and_orientation_fail_closed(self):
        d = self.base(9537699, "SHORT"); d["duration_seconds"] = 181
        self.assertIn("SHORT_TOO_LONG", validate_youtube_upload(YouTubeUploadRequest(**d))["blockers"])
        d = self.base(9537702, "LONG_VIDEO"); d["duration_seconds"] = 180
        self.assertIn("LONG_VIDEO_TOO_SHORT", validate_youtube_upload(YouTubeUploadRequest(**d))["blockers"])

    def test_wrong_format_and_no_authorization_block(self):
        d = self.base(9537699, "SHORT"); d["format"] = "LONG_VIDEO"; d["authorized"] = False
        out = validate_youtube_upload(YouTubeUploadRequest(**d))
        self.assertIn("FORMAT_MISMATCH", out["blockers"])
        self.assertIn("SIGNATURE_REQUIRED", out["blockers"])
        self.assertFalse(out["external_action_allowed"])


if __name__ == "__main__":
    unittest.main()
