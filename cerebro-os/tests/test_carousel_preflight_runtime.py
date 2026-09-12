import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from carousel_preflight import CarouselPhoto, CarouselPreflightRequest, evaluate_carousel_preflight


class CarouselPreflightRuntimeTests(unittest.TestCase):
    def req(self, **changes):
        photos = (
            CarouselPhoto("a1", "https://example.com/1.jpg", 1, True),
            CarouselPhoto("a2", "https://example.com/2.jpg", 2, True),
        )
        data = dict(
            company_id="fenix-capital",
            engine_id="SOCIAL-PUBLISH",
            environment="LAB",
            version="1.0.0",
            publication_id="pub-1",
            production_order_id="po-1",
            programming_id="prog-1",
            run_id="run-1",
            copy_reviewed=True,
            qa_approved=True,
            real_publish_authorized=False,
            photos=photos,
        )
        data.update(changes)
        return CarouselPreflightRequest(**data)

    def test_old_gate_validates_two_to_thirty_photos_and_never_calls_facebook(self):
        result = evaluate_carousel_preflight(self.req())
        self.assertEqual(result["status"], "DIRECT_CONTRACT_VALIDATED")
        self.assertEqual(result["platform_state"], "FACEBOOK_NOT_CALLED")
        self.assertFalse(result["requires_human"])
        self.assertFalse(result["external_action_allowed"])

    def test_single_photo_or_authorized_real_publish_is_blocked(self):
        single = (CarouselPhoto("a1", "https://example.com/1.jpg", 1, True),)
        self.assertEqual(evaluate_carousel_preflight(self.req(photos=single))["status"], "BLOCKED_PREFLIGHT")
        self.assertEqual(evaluate_carousel_preflight(self.req(real_publish_authorized=True))["status"], "BLOCKED_PREFLIGHT")

    def test_photo_qa_and_unique_positions_are_fail_closed_extensions(self):
        bad_qa = (
            CarouselPhoto("a1", "https://example.com/1.jpg", 1, True),
            CarouselPhoto("a2", "https://example.com/2.jpg", 2, False),
        )
        duplicate_pos = (
            CarouselPhoto("a1", "https://example.com/1.jpg", 1, True),
            CarouselPhoto("a2", "https://example.com/2.jpg", 1, True),
        )
        self.assertTrue(evaluate_carousel_preflight(self.req(photos=bad_qa))["requires_human"])
        self.assertTrue(evaluate_carousel_preflight(self.req(photos=duplicate_pos))["requires_human"])

    def test_scope_is_explicit(self):
        result = evaluate_carousel_preflight(self.req(environment="PREPROD"))
        self.assertEqual(result["company_id"], "fenix-capital")
        self.assertEqual(result["environment"], "PREPROD")
        self.assertEqual(result["version"], "1.0.0")
        with self.assertRaises(ValueError):
            evaluate_carousel_preflight(self.req(environment="DEV"))


if __name__ == "__main__":
    unittest.main()
