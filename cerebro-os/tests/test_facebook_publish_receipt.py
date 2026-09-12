import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.facebook_publish_receipt import ReceiptInput, normalize_receipt


class FacebookPublishReceiptTests(unittest.TestCase):
    def base(self, **overrides):
        data = dict(
            company_id="fenix",
            engine_id="SOC-PUB-FB",
            environment="PROD",
            version="v1",
            publication_id="pub-1",
            run_id="run-1",
            format="text",
            external_id="fb-123",
            permalink="https://facebook.example/post",
            notion_return_ok=True,
            platform_confirmed=True,
        )
        data.update(overrides)
        return ReceiptInput(**data)

    def test_text_commits_after_notion_return(self):
        out = normalize_receipt(self.base())
        self.assertEqual(out["receipt_status"], "FACEBOOK_ACCEPTED")
        self.assertEqual(out["idempotency_status"], "COMMITTED")
        self.assertEqual(out["override_status"], "CONSUMED")
        self.assertTrue(out["analytics_windows_ready"])
        self.assertFalse(out["external_action_allowed"])
        self.assertFalse(out["facebook_called_by_runtime"])
        self.assertFalse(out["notion_mutation_allowed"])

    def test_image_preserves_photo_id(self):
        out = normalize_receipt(self.base(format="image", photo_id="photo-9"))
        self.assertEqual(out["photo_id"], "photo-9")
        self.assertEqual(out["idempotency_status"], "COMMITTED")

    def test_reel_processing_holds_idempotency(self):
        out = normalize_receipt(self.base(format="reel", platform_confirmed=False, notion_return_ok=False))
        self.assertEqual(out["receipt_status"], "FACEBOOK_UPLOAD_ACCEPTED_PROCESSING")
        self.assertEqual(out["idempotency_status"], "PENDING_PLATFORM_CONFIRMATION")
        self.assertEqual(out["notion_state"], "Pendiente de publicar")
        self.assertFalse(out["analytics_windows_ready"])

    def test_video_long_processing_holds_idempotency(self):
        out = normalize_receipt(self.base(format="video_long", platform_confirmed=False, notion_return_ok=False))
        self.assertEqual(out["receipt_status"], "VIDEO_PROCESSING")
        self.assertEqual(out["idempotency_status"], "PENDING_PLATFORM_CONFIRMATION")

    def test_missing_notion_return_keeps_lock(self):
        out = normalize_receipt(self.base(format="link", notion_return_ok=False))
        self.assertEqual(out["idempotency_status"], "LOCKED_PENDING_NOTION_RETURN")
        self.assertEqual(out["notion_state"], "PENDING_RETURN")
        self.assertFalse(out["analytics_windows_ready"])

    def test_non_prod_receipt_fails_closed(self):
        out = normalize_receipt(self.base(environment="TEST"))
        self.assertEqual(out["receipt_status"], "PROD_RECEIPT_OUTSIDE_PROD")
        self.assertTrue(out["requires_human"])
        self.assertEqual(out["human_reason"], "POLICY_CONFLICT")

    def test_unknown_format_fails_closed(self):
        out = normalize_receipt(self.base(format="unknown"))
        self.assertEqual(out["receipt_status"], "UNSUPPORTED_FORMAT")
        self.assertEqual(out["human_reason"], "LOW_CONFIDENCE")

    def test_all_supported_formats_never_allow_external_action(self):
        for fmt in ("text", "link", "image", "reel", "carousel", "video_long"):
            confirmed = fmt not in {"reel", "video_long"}
            out = normalize_receipt(self.base(format=fmt, platform_confirmed=confirmed))
            self.assertFalse(out["external_action_allowed"], fmt)
            self.assertFalse(out["facebook_called_by_runtime"], fmt)


if __name__ == "__main__":
    unittest.main()
