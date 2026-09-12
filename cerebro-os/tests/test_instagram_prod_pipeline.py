import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from instagram_prod_pipeline import InstagramPublishInput, InstagramReceiptInput, assess_instagram_publish, normalize_instagram_receipt


def pub(scenario_id, **kwargs):
    base = dict(
        scenario_id=scenario_id,
        company_id="fenix",
        engine_id="instagram-prod",
        environment="PROD",
        version="v1",
        publication_id="pub-1",
        run_id="run-1",
        engine_enabled=True,
        override_authorized_once=True,
        override_record_matches=True,
        idempotency_clear=True,
        explicit_authorized=True,
        caption_present=True,
    )
    base.update(kwargs)
    return InstagramPublishInput(**base)


def receipt(scenario_id, **kwargs):
    base = dict(
        scenario_id=scenario_id,
        company_id="fenix",
        engine_id="instagram-prod",
        environment="PROD",
        version="v1",
        publication_id="pub-1",
        run_id="run-1",
        external_id="media-1",
        permalink="https://instagram.example/p/1",
        notion_return_ok=True,
    )
    base.update(kwargs)
    return InstagramReceiptInput(**base)


class InstagramProdPipelineTest(unittest.TestCase):
    def test_image_ready_but_never_auto_executes(self):
        out = assess_instagram_publish(pub(9534139, image_url_present=True))
        self.assertEqual(out["status"], "READY_FOR_EXPLICIT_EXECUTION")
        self.assertEqual(out["human_reason"], "SIGNATURE_REQUIRED")
        self.assertFalse(out["external_action_allowed"])

    def test_reel_requires_video_and_share_to_feed_field(self):
        out = assess_instagram_publish(pub(9534087, video_url_present=False, share_to_feed_present=False))
        self.assertEqual(out["status"], "BLOCKED_INPUT_CONTRACT")
        self.assertIn("video_url_present", out["failed_gates"])
        self.assertIn("share_to_feed_present", out["failed_gates"])

    def test_carousel_preserves_make_2_to_10_contract(self):
        good = assess_instagram_publish(pub(9534084, files_count=10))
        self.assertEqual(good["status"], "READY_FOR_EXPLICIT_EXECUTION")
        bad = assess_instagram_publish(pub(9534084, files_count=11))
        self.assertIn("files_count_2_10", bad["failed_gates"])

    def test_authorization_missing_is_human_gate(self):
        out = assess_instagram_publish(pub(9534139, image_url_present=True, explicit_authorized=False))
        self.assertEqual(out["human_reason"], "SIGNATURE_REQUIRED")
        self.assertFalse(out["instagram_mutation_allowed"])

    def test_confirmed_receipt_commits_after_notion(self):
        out = normalize_instagram_receipt(receipt(9534139))
        self.assertEqual(out["status"], "POST_PUBLISH_COMMITTED")
        self.assertEqual(out["idempotency_state"], "COMMITTED")
        self.assertEqual(out["override_state"], "CONSUMED")
        self.assertFalse(out["retry_publish_allowed"])

    def test_notion_pending_never_republishes(self):
        out = normalize_instagram_receipt(receipt(9534087, notion_return_ok=False))
        self.assertEqual(out["status"], "INSTAGRAM_CONFIRMED_NOTION_PENDING")
        self.assertEqual(out["idempotency_state"], "HOLD_UNTIL_NOTION_RETURN")
        self.assertFalse(out["retry_publish_allowed"])

    def test_carousel_receipt_validates_album_count(self):
        bad = normalize_instagram_receipt(receipt(9534084, album_items_count=11))
        self.assertEqual(bad["status"], "CAROUSEL_ITEM_COUNT_MISMATCH")
        good = normalize_instagram_receipt(receipt(9534084, album_items_count=2))
        self.assertEqual(good["status"], "POST_PUBLISH_COMMITTED")

    def test_non_prod_fail_closed(self):
        out = assess_instagram_publish(pub(9534139, image_url_present=True, environment="TEST"))
        self.assertEqual(out["status"], "ENVIRONMENT_NOT_PROD")
        self.assertEqual(out["human_reason"], "POLICY_CONFLICT")


if __name__ == "__main__":
    unittest.main()
