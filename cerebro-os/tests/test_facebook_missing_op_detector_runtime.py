import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))

from facebook_missing_op_detector import FacebookMissingOpRequest, detect_missing_production_order


class FacebookMissingOpDetectorTests(unittest.TestCase):
    def base(self, **overrides):
        data = dict(
            company_id="fenix-capital",
            engine_id="SOC-FB-MISSING-OP",
            environment="TEST",
            version="1.0",
            publication_id="pub-1",
            format_name="Texto orgánico simple",
            publication_state="Pendiente de publicar",
            production_order_id=None,
        )
        data.update(overrides)
        return FacebookMissingOpRequest(**data)

    def test_missing_op_blocks_and_never_calls_facebook(self):
        result = detect_missing_production_order(self.base())
        self.assertEqual(result["status"], "BLOCKED_OP_RELATION_MISSING")
        self.assertEqual(result["difference"], "OP_RELATION_MISSING")
        self.assertTrue(result["requires_human"])
        self.assertEqual(result["human_reason"], "LOW_CONFIDENCE")
        self.assertFalse(result["external_action_allowed"])
        self.assertEqual(result["platform_state"], "NOT_CALLED")

    def test_existing_op_is_not_blocked(self):
        result = detect_missing_production_order(self.base(production_order_id="op-123"))
        self.assertEqual(result["status"], "OP_RELATION_PRESENT")
        self.assertFalse(result["requires_human"])
        self.assertFalse(result["external_action_allowed"])

    def test_non_target_record_is_not_applicable(self):
        result = detect_missing_production_order(self.base(format_name="Imagen"))
        self.assertEqual(result["status"], "NOT_APPLICABLE")
        self.assertFalse(result["external_action_allowed"])

    def test_invalid_environment_fails_closed(self):
        with self.assertRaises(ValueError):
            detect_missing_production_order(self.base(environment="UNKNOWN"))


if __name__ == "__main__":
    unittest.main()
