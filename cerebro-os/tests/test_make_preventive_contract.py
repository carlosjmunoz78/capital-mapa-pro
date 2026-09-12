import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from make_preventive_contract import (
    DlqRecoveryObservation,
    PreventiveGateState,
    assess_facebook_test_gate,
    assess_safe_retry,
)


class MakePreventiveContractTests(unittest.TestCase):
    def test_facebook_gate_allows_only_test_read_path(self):
        out = assess_facebook_test_gate(
            PreventiveGateState(
                company_id="fenix-capital",
                engine_id="PREVENTIVE-FB-GATE",
                environment="TEST",
                version="1.0.0",
                global_status="BLOCKED_BY_DEFAULT",
                facebook_status="TEST_ONLY",
            )
        )
        self.assertEqual(out["status"], "ALLOWED_TEST")
        self.assertTrue(out["read_only_allowed"])
        self.assertFalse(out["publication_allowed"])
        self.assertFalse(out["external_mutation_allowed"])

    def test_facebook_gate_fail_closed(self):
        out = assess_facebook_test_gate(
            PreventiveGateState(
                company_id="fenix-capital",
                engine_id="PREVENTIVE-FB-GATE",
                environment="TEST",
                version="1.0.0",
                global_status="ENABLED",
                facebook_status="PROD",
            )
        )
        self.assertEqual(out["status"], "BLOCKED")
        self.assertFalse(out["read_only_allowed"])

    def test_dlq_safe_retry_is_read_only(self):
        out = assess_safe_retry(
            DlqRecoveryObservation(
                company_id="fenix-capital",
                engine_id="DLQ-RECOVERY",
                environment="TEST",
                version="1.0.0",
                operation_type="analytics_capture",
                platform_state="TEMPORARY_TIMEOUT",
                attempts=1,
                max_attempts=3,
                idempotency_clear=True,
            )
        )
        self.assertEqual(out["status"], "SAFE_RETRY_APPROVED")
        self.assertTrue(out["retry_read_allowed"])
        self.assertFalse(out["retry_publish_allowed"])
        self.assertFalse(out["notion_mutation_allowed"])

    def test_dlq_retry_blocks_non_read_operation(self):
        out = assess_safe_retry(
            DlqRecoveryObservation(
                company_id="fenix-capital",
                engine_id="DLQ-RECOVERY",
                environment="TEST",
                version="1.0.0",
                operation_type="publish",
                platform_state="TEMPORARY_TIMEOUT",
                attempts=1,
                max_attempts=3,
                idempotency_clear=True,
            )
        )
        self.assertEqual(out["status"], "RETRY_BLOCKED")
        self.assertFalse(out["retry_read_allowed"])


if __name__ == "__main__":
    unittest.main()
