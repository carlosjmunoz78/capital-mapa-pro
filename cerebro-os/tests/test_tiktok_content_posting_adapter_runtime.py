import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from tiktok_content_posting_adapter import TikTokDirectPostPlan, build_direct_post_plan


class TikTokContentPostingAdapterTests(unittest.TestCase):
    def base(self):
        return dict(
            company_id="fenix",
            engine_id="tiktok",
            environment="PROD",
            version="1",
            publication_id="pub",
            run_id="run",
            title="contenido",
            privacy_level="SELF_ONLY",
            video_size=10_000_000,
            chunk_size=10_000_000,
            total_chunk_count=1,
            access_token_ref_present=True,
            creator_consent=True,
            scope_approved=True,
            user_authorized_scope=True,
        )

    def test_ready_plan_is_still_explicit_and_fail_closed(self):
        out = build_direct_post_plan(TikTokDirectPostPlan(**self.base()))
        self.assertEqual(out["status"], "READY_FOR_EXPLICIT_EXECUTION")
        self.assertEqual(out["required_scope"], "video.publish")
        self.assertEqual(out["creator_info_path"], "/v2/post/publish/creator_info/query/")
        self.assertEqual(out["direct_post_video_init_path"], "/v2/post/publish/video/init/")
        self.assertEqual(out["post_status_path"], "/v2/post/publish/status/fetch/")
        self.assertFalse(out["external_action_allowed"])
        self.assertEqual(out["human_reason"], "SIGNATURE_REQUIRED")

    def test_missing_scope_and_oauth_block(self):
        data = self.base()
        data["access_token_ref_present"] = False
        data["scope_approved"] = False
        data["user_authorized_scope"] = False
        out = build_direct_post_plan(TikTokDirectPostPlan(**data))
        self.assertEqual(out["status"], "BLOCKED")
        self.assertIn("MISSING_CREDENTIAL", out["blockers"])
        self.assertIn("PERMISSION_REQUIRED", out["blockers"])
        self.assertEqual(out["human_reason"], "PERMISSION_REQUIRED")

    def test_no_secret_value_is_requested_by_contract(self):
        out = build_direct_post_plan(TikTokDirectPostPlan(**self.base()))
        self.assertFalse(out["secret_value_required_in_runtime_input"])


if __name__ == "__main__":
    unittest.main()
