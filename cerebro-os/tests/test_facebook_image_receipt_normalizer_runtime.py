import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))

from facebook_image_receipt_normalizer import ImageReceiptNormalizeRequest, normalize_image_receipt


class ImageReceiptNormalizerTests(unittest.TestCase):
    def base(self, **overrides):
        data = dict(
            company_id="fenix",
            engine_id="SOCIAL-FB",
            environment="PROD",
            version="V1",
            publication_id="pub-1",
            run_id="run-1",
            canonical_receipt_exists=False,
            source_receipt_exists=True,
            external_id="post-1",
            page_id="page-1",
        )
        data.update(overrides)
        return ImageReceiptNormalizeRequest(**data)

    def test_existing_canonical_receipt_is_idempotent(self):
        result = normalize_image_receipt(self.base(canonical_receipt_exists=True))
        self.assertEqual("CANONICAL_RECEIPT_ALREADY_EXISTS", result["status"])
        self.assertFalse(result["facebook_called"])

    def test_missing_source_receipt_fails_closed(self):
        result = normalize_image_receipt(self.base(source_receipt_exists=False))
        self.assertEqual("BLOCKED_SOURCE_RECEIPT_MISSING", result["status"])
        self.assertEqual("LOW_CONFIDENCE", result["human_reason"])

    def test_normalization_never_calls_facebook(self):
        result = normalize_image_receipt(self.base())
        self.assertEqual("CANONICAL_RECEIPT_CREATED", result["status"])
        self.assertEqual("FACEBOOK_ACCEPTED", result["canonical_status"])
        self.assertTrue(result["analytics_windows_enabled"])
        self.assertFalse(result["facebook_called"])
        self.assertFalse(result["external_action_allowed"])


if __name__ == "__main__":
    unittest.main()
