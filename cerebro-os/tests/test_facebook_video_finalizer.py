import os
import sys
import unittest

HERE = os.path.dirname(__file__)
RUNTIME = os.path.abspath(os.path.join(HERE, "..", "runtime"))
if RUNTIME not in sys.path:
    sys.path.insert(0, RUNTIME)

from facebook_video_finalizer import VideoFinalizerInput, finalize_video


class FacebookVideoFinalizerTests(unittest.TestCase):
    def base(self, **overrides):
        data = dict(
            company_id="fenix",
            engine_id="facebook-publish",
            environment="PROD",
            version="1",
            publication_id="pub-1",
            run_id="run-1",
            kind="reel",
            external_id="vid-1",
            published=False,
            platform_status="processing",
            permalink_url="",
        )
        data.update(overrides)
        return VideoFinalizerInput(**data)

    def test_reel_processing_never_reuploads(self):
        out = finalize_video(self.base())
        self.assertEqual(out["state"], "PLATFORM_PROCESSING")
        self.assertTrue(out["poll_only"])
        self.assertFalse(out["retry_upload_allowed"])
        self.assertFalse(out["facebook_mutation_allowed"])

    def test_reel_confirms_only_with_permalink(self):
        out = finalize_video(self.base(published=True, platform_status="ready", permalink_url="/reel/abc"))
        self.assertEqual(out["state"], "PUBLISHED_CONFIRMED")
        self.assertTrue(out["canonical_receipt_ready"])
        self.assertEqual(out["idempotency_state"], "COMMIT_AFTER_NOTION_RETURN")
        self.assertFalse(out["analytics_windows_ready_after_commit"] is False)

    def test_reel_published_without_permalink_stays_processing(self):
        out = finalize_video(self.base(published=True, platform_status="ready", permalink_url=""))
        self.assertEqual(out["state"], "PLATFORM_PROCESSING")
        self.assertFalse(out["retry_upload_allowed"])

    def test_long_video_requires_ready(self):
        out = finalize_video(self.base(kind="video_long", published=True, platform_status="processing"))
        self.assertEqual(out["state"], "PLATFORM_PROCESSING")
        out2 = finalize_video(self.base(kind="video_long", published=True, platform_status="ready"))
        self.assertEqual(out2["state"], "PUBLISHED_CONFIRMED")

    def test_wrong_environment_fail_closed(self):
        out = finalize_video(self.base(environment="TEST"))
        self.assertTrue(out["human_required"])
        self.assertEqual(out["human_reason"], "POLICY_CONFLICT")
        self.assertFalse(out["external_action_allowed"])

    def test_unknown_kind_fail_closed(self):
        out = finalize_video(self.base(kind="story"))
        self.assertTrue(out["human_required"])
        self.assertEqual(out["human_reason"], "LOW_CONFIDENCE")


if __name__ == "__main__":
    unittest.main()
