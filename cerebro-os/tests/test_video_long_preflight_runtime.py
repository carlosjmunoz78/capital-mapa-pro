import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from video_long_preflight import VideoLongPreflightRequest, evaluate_video_long_preflight


class VideoLongPreflightRuntimeTests(unittest.TestCase):
    def req(self, **changes):
        data = dict(
            company_id="fenix",
            engine_id="SOCIAL-PUBLISH",
            environment="LAB",
            version="1.0.0",
            publication_id="pub-1",
            run_id="run-1",
            video_url="https://example.com/video.mp4",
            mime="video/mp4",
            duration_seconds=120,
            width=1080,
            height=1920,
            qa_approved=True,
            real_publish_authorized=False,
            http_status=200,
        )
        data.update(changes)
        return VideoLongPreflightRequest(**data)

    def test_old_contract_validates_without_calling_facebook(self):
        result = evaluate_video_long_preflight(self.req())
        self.assertEqual(result["status"], "DIRECT_CONTRACT_VALIDATED")
        self.assertEqual(result["platform_state"], "FACEBOOK_NOT_CALLED")
        self.assertFalse(result["external_action_allowed"])

    def test_http_duration_qa_and_publish_authorization_fail_closed(self):
        for changes in (
            {"http_status": 404},
            {"duration_seconds": 90},
            {"qa_approved": False},
            {"real_publish_authorized": True},
        ):
            result = evaluate_video_long_preflight(self.req(**changes))
            self.assertEqual(result["status"], "BLOCKED_PREFLIGHT")
            self.assertFalse(result["external_action_allowed"])

    def test_scope_is_mandatory(self):
        with self.assertRaises(ValueError):
            evaluate_video_long_preflight(self.req(environment="DEV"))


if __name__ == "__main__":
    unittest.main()
