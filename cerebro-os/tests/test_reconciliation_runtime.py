import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from reconciliation import ReconciliationInput, reconcile


class ReconciliationRuntimeTests(unittest.TestCase):
    def item(self, **changes):
        data = dict(company_id="fenix-capital", engine_id="RECON-001", environment="LAB", version="1.1.0", router_status="ROUTED", log_status="OK", capture_status="CAPTURED_PARTIAL", quality_status="PARTIAL_DATA_REVIEW", notion_state="Capturada")
        data.update(changes)
        return ReconciliationInput(**data)

    def test_partial_capture_consistency_and_human_flag(self):
        result = reconcile(self.item())
        self.assertEqual(result["status"], "CONSISTENT_CAPTURED_PARTIAL_HOLD")
        self.assertEqual(result["difference"], "LEARNING_BLOCKED_PARTIAL_DATA")
        self.assertTrue(result["requires_human"])
        self.assertFalse(result["learning_allowed"])
        self.assertFalse(result["external_action_allowed"])

    def test_early_capture_and_waiting_paths(self):
        result = reconcile(self.item(capture_status="REJECTED_EARLY_CAPTURE", quality_status="WAITING_CAPTURE"))
        self.assertEqual(result["status"], "CONSISTENT_ROLLBACK_PENDING_RECAPTURE")
        self.assertEqual(result["difference"], "TIMEZONE_ROLLBACK_PENDING_RECAPTURE")
        result = reconcile(self.item(capture_status="PENDING", quality_status="WAITING_CAPTURE"))
        self.assertEqual(result["status"], "CONSISTENT_WAITING_CAPTURE")

    def test_scope_is_enforced(self):
        with self.assertRaises(ValueError):
            reconcile(self.item(environment="DEV"))


if __name__ == "__main__":
    unittest.main()
