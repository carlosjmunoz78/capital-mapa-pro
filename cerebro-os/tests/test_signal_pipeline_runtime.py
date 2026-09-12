import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from signal_pipeline import SignalInput, build_signal_pipeline_plan


class SignalPipelineRuntimeTests(unittest.TestCase):
    def signal(self, **changes):
        data = dict(company_id="fenix-capital", engine_id="CEREBRO-SIGNAL", environment="LAB", version="2.2.0", signal_id="S1", title="Idea", summary="Resumen", source="Research", buyer_persona="Inversor", funnel_phase="Consideración", objective="Captar lead", recommended_content="Guía", avoid_content="Promesas", priority="Alta", recommendation="Probar contenido")
        data.update(changes)
        return SignalInput(**data)

    def test_plan_preserves_four_stage_contract_without_external_write(self):
        result = build_signal_pipeline_plan(self.signal())
        self.assertEqual(result["status"], "PLAN_READY_NO_EXTERNAL_WRITE")
        self.assertIn("SIGNAL_ID=S1", result["idea"]["summary"])
        self.assertEqual(result["evaluation"]["decision_state"], "En análisis")
        self.assertEqual(result["laboratory"]["environment"], "TEST")
        self.assertFalse(result["external_action_allowed"])
        self.assertTrue(result["requires_human"])

    def test_duplicate_is_blocked_before_any_plan(self):
        result = build_signal_pipeline_plan(self.signal(), duplicate_exists=True)
        self.assertEqual(result["status"], "BLOCKED_DUPLICATE")
        self.assertFalse(result["external_action_allowed"])

    def test_scope_is_part_of_idempotency(self):
        lab = build_signal_pipeline_plan(self.signal(environment="LAB"))["idempotency_key"]
        prod = build_signal_pipeline_plan(self.signal(environment="PROD"))["idempotency_key"]
        self.assertNotEqual(lab, prod)


if __name__ == "__main__":
    unittest.main()
