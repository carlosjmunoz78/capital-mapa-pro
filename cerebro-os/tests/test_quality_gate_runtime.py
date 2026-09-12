import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from quality_gate import QualityInput, evaluate_quality_gate


class QualityGateRuntimeTests(unittest.TestCase):
    def base(self, **changes):
        now = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)
        data = dict(
            company_id="fenix-capital",
            engine_id="SOC-QUALITY",
            environment="LAB",
            version="1.1.0",
            measurement_window="24h",
            expected_capture_at=now - timedelta(hours=1),
            analytics_state="Capturada",
            data_quality="Completa",
            human_validation="Validada",
            eligible_for_cerebro=True,
        )
        data.update(changes)
        return now, QualityInput(**data)

    def test_exact_status_precedence_and_learning_gate(self):
        now, item = self.base(expected_capture_at=datetime(2026, 9, 12, 13, 0, tzinfo=timezone.utc))
        self.assertEqual(evaluate_quality_gate(item, now=now)["status"], "WAITING_CAPTURE")
        now, item = self.base(analytics_state="Pendiente")
        self.assertEqual(evaluate_quality_gate(item, now=now)["status"], "TECHNICAL_REVIEW")
        now, item = self.base(data_quality="Parcial")
        self.assertEqual(evaluate_quality_gate(item, now=now)["status"], "PARTIAL_DATA_REVIEW")
        now, item = self.base(human_validation="Pendiente")
        result = evaluate_quality_gate(item, now=now)
        self.assertEqual(result["status"], "HUMAN_REVIEW")
        self.assertTrue(result["requires_human"])
        now, item = self.base(eligible_for_cerebro=False)
        self.assertEqual(evaluate_quality_gate(item, now=now)["status"], "HOLD_NOT_ELIGIBLE")
        now, item = self.base()
        result = evaluate_quality_gate(item, now=now)
        self.assertEqual(result["status"], "ELIGIBLE_FOR_LEARNING")
        self.assertTrue(result["learning_allowed"])

    def test_scope_is_mandatory(self):
        now, item = self.base(environment="DEV")
        with self.assertRaises(ValueError):
            evaluate_quality_gate(item, now=now)


if __name__ == "__main__":
    unittest.main()
