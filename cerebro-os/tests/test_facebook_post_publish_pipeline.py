import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from facebook_post_publish_pipeline import (
    FacebookPostPublishPipelineInput,
    evaluate_facebook_post_publish_pipeline,
)


class FacebookPostPublishPipelineTests(unittest.TestCase):
    def base(self, **overrides):
        data = dict(
            company_id="fenix",
            engine_id="facebook-publish",
            environment="PROD",
            version="v1",
            publication_id="pub-1",
            run_id="run-1",
            format="text",
            external_id="fb-123",
            published_at="2026-09-12T12:00:00Z",
            permalink="https://facebook.example/post/123",
            platform_confirmed=True,
            notion_return_ok=False,
            override_consumed=False,
            idempotency_committed=False,
            canonical_receipt_exists=False,
            windows_exist=False,
        )
        data.update(overrides)
        return FacebookPostPublishPipelineInput(**data)

    def test_waits_for_platform_confirmation_without_retrying_upload(self):
        out = evaluate_facebook_post_publish_pipeline(
            self.base(format="reel", platform_confirmed=False)
        )
        self.assertEqual(out["pipeline_state"], "PLATFORM_CONFIRMATION_PENDING")
        self.assertFalse(out["retry_publish_allowed"])
        self.assertFalse(out["analytics_windows_ready"])
        self.assertFalse(out["external_action_allowed"])

    def test_waits_for_notion_return(self):
        out = evaluate_facebook_post_publish_pipeline(self.base())
        self.assertEqual(out["pipeline_state"], "NOTION_RETURN_PENDING")
        self.assertFalse(out["analytics_windows_ready"])
        self.assertFalse(out["notion_mutation_allowed"])

    def test_override_gap_is_human_policy_conflict(self):
        out = evaluate_facebook_post_publish_pipeline(
            self.base(notion_return_ok=True, override_consumed=False)
        )
        self.assertEqual(out["pipeline_state"], "OVERRIDE_CONSUMPTION_PENDING")
        self.assertTrue(out["requires_human"])
        self.assertEqual(out["human_reason"], "POLICY_CONFLICT")

    def test_waits_for_idempotency_commit(self):
        out = evaluate_facebook_post_publish_pipeline(
            self.base(notion_return_ok=True, override_consumed=True, idempotency_committed=False)
        )
        self.assertEqual(out["pipeline_state"], "IDEMPOTENCY_COMMIT_PENDING")
        self.assertFalse(out["analytics_windows_ready"])

    def test_committed_state_plans_analytics_windows(self):
        out = evaluate_facebook_post_publish_pipeline(
            self.base(
                notion_return_ok=True,
                override_consumed=True,
                idempotency_committed=True,
                canonical_receipt_exists=True,
            )
        )
        self.assertEqual(out["pipeline_state"], "POST_PUBLISH_COMMITTED")
        self.assertTrue(out["analytics_windows_ready"])
        self.assertEqual(out["analytics"]["status"], "WINDOWS_READY_TO_CREATE")
        self.assertEqual(out["analytics"]["idempotency_key"], "FACEBOOK|ANALYTICS_WINDOWS|pub-1")
        self.assertFalse(out["external_action_allowed"])
        self.assertFalse(out["facebook_mutation_allowed"])
        self.assertFalse(out["notion_mutation_allowed"])

    def test_existing_windows_block_duplicate_creation(self):
        out = evaluate_facebook_post_publish_pipeline(
            self.base(
                notion_return_ok=True,
                override_consumed=True,
                idempotency_committed=True,
                canonical_receipt_exists=True,
                windows_exist=True,
            )
        )
        self.assertEqual(out["analytics"]["status"], "BLOCKED_EXISTING_WINDOWS")
        self.assertFalse(out["analytics_windows_ready"])

    def test_non_prod_fails_closed(self):
        out = evaluate_facebook_post_publish_pipeline(self.base(environment="TEST"))
        self.assertTrue(out["requires_human"])
        self.assertEqual(out["human_reason"], "POLICY_CONFLICT")
        self.assertFalse(out["external_action_allowed"])

    def test_all_supported_formats_reach_committed_state(self):
        for fmt in ("text", "link", "image", "reel", "carousel", "video_long"):
            with self.subTest(fmt=fmt):
                out = evaluate_facebook_post_publish_pipeline(
                    self.base(
                        format=fmt,
                        notion_return_ok=True,
                        override_consumed=True,
                        idempotency_committed=True,
                        canonical_receipt_exists=True,
                    )
                )
                self.assertEqual(out["pipeline_state"], "POST_PUBLISH_COMMITTED")
                self.assertTrue(out["analytics_windows_ready"])
                self.assertFalse(out["retry_publish_allowed"])


if __name__ == "__main__":
    unittest.main()
