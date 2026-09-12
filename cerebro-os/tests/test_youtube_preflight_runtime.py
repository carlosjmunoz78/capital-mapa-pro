import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from youtube_preflight import YouTubePreflightRequest, plan_youtube_preflight


class YouTubePreflightRuntimeTests(unittest.TestCase):
    def req(self, **changes):
        data = dict(
            company_id="fenix",
            engine_id="SOCIAL",
            environment="LAB",
            version="1.0.0",
            publication_id="pub-1",
            run_id="run-1",
            format="short",
            channel_id="UC0XL5bW9A6vXfNc5EDIN0Ig",
            privacy_status="private",
            content_ready=True,
            asset_ready=True,
            qa_passed=True,
            schedule_ready=True,
            duplicate_exists=False,
        )
        data.update(changes)
        return YouTubePreflightRequest(**data)

    def test_short_routes_but_never_executes(self):
        result = plan_youtube_preflight(self.req())
        self.assertEqual(result["status"], "ROUTED_WITH_ENGINE_DISABLED")
        self.assertEqual(result["preflight_status"], "PREFLIGHT_READY_PUBLISH_BLOCKED")
        self.assertFalse(result["external_action_allowed"])
        self.assertEqual(result["post_video_id_steps"], ["thumbnail", "playlist", "captions", "processing"])

    def test_community_stays_manual(self):
        result = plan_youtube_preflight(self.req(format="community"))
        self.assertEqual(result["status"], "QUEUED_MANUAL_COMMUNITY")
        self.assertFalse(result["external_action_allowed"])

    def test_wrong_channel_duplicate_and_missing_gate_block(self):
        self.assertEqual(plan_youtube_preflight(self.req(channel_id="wrong"))["status"], "BLOCKED_WRONG_CHANNEL")
        self.assertEqual(plan_youtube_preflight(self.req(duplicate_exists=True))["status"], "BLOCKED_DUPLICATE")
        self.assertEqual(plan_youtube_preflight(self.req(asset_ready=False))["status"], "BLOCKED_PREFLIGHT")

    def test_scope_is_explicit(self):
        result = plan_youtube_preflight(self.req(environment="PROD"))
        self.assertEqual(result["company_id"], "fenix")
        self.assertEqual(result["environment"], "PROD")
        self.assertEqual(result["version"], "1.0.0")

    def test_invalid_environment_rejected(self):
        with self.assertRaises(ValueError):
            plan_youtube_preflight(self.req(environment="DEV"))


if __name__ == "__main__":
    unittest.main()
