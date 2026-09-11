import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

evaluation = load("cerebro_evaluation", "quality/evaluation.py")
tribunal = load("cerebro_tribunal", "quality/tribunal.py")
records = load("cerebro_observability", "observability/records.py")
supervisor = load("cerebro_supervisor", "supervisor/supervisor.py")

class QualityObservabilityTests(unittest.TestCase):
    def test_evaluation_needs_evidence_and_scope(self):
        result = evaluation.EvaluationResult("FACT-001", 1.0, 0.9, ())
        self.assertFalse(result.passed)
        evidenced = evaluation.EvaluationResult(
            "FACT-001", 1.0, 0.9, ("ci://run/1",),
            company_id="fenix-capital", environment="PROD", version="2.0.0",
        )
        self.assertTrue(evidenced.passed)
        self.assertTrue(evaluation.aggregate((evidenced,), company_id="fenix-capital", environment="PROD", version="2.0.0"))
        self.assertFalse(evaluation.aggregate((evidenced,), company_id="other", environment="PROD", version="2.0.0"))
        self.assertFalse(evaluation.aggregate((evidenced,), company_id="fenix-capital", environment="LAB", version="2.0.0"))
        with self.assertRaises(ValueError):
            evaluation.EvaluationResult("FACT-001", 1.0, 0.9, ("e",), environment="DEV").validate()

    def test_tribunal_rejects_missing_gate(self):
        gates = {gate: True for gate in tribunal.REQUIRED_GATES}
        gates["rollback"] = False
        evidence = {gate: f"e:{gate}" for gate in tribunal.REQUIRED_GATES}
        decision = tribunal.TribunalDecision("FACT-001", gates, evidence_refs=evidence, version="2.0.0")
        self.assertFalse(decision.approved)
        self.assertEqual(decision.missing(), ("rollback",))

    def test_tribunal_approves_all_gates_only_with_valid_scope(self):
        gates = {gate: True for gate in tribunal.REQUIRED_GATES}
        evidence = {gate: f"e:{gate}" for gate in tribunal.REQUIRED_GATES}
        self.assertTrue(tribunal.TribunalDecision("FACT-001", gates, company_id="fenix", environment="PROD", evidence_refs=evidence, version="2.0.0").approved)
        self.assertFalse(tribunal.TribunalDecision("FACT-001", gates, company_id="fenix", environment="PROD", evidence_refs=evidence, version="").approved)
        self.assertFalse(tribunal.TribunalDecision("FACT-001", gates, company_id="fenix", environment="DEV", evidence_refs=evidence, version="2.0.0").approved)

    def test_observability_record_validates(self):
        record = records.ExecutionRecord(
            company_id="fenix-capital", engine_id="FACT-001", version="0.1.0",
            environment="LAB", action="scaffold", result="success",
            evidence_ref="ci://run/1", duration_ms=12, cost_eur=0.0,
        )
        record.validate()
        with self.assertRaises(ValueError):
            records.ExecutionRecord(
                company_id="fenix-capital", engine_id="FACT-001", version="0.1.0",
                environment="DEV", action="scaffold", result="success",
                evidence_ref="ci://run/1", duration_ms=12,
            ).validate()

    def test_supervisor_requires_all_green_and_version_scope(self):
        red = supervisor.EngineHealth("FACT-001", True, True, True, False, True)
        evidence = ("tests:e", "evaluation:e", "tribunal:e", "rollback:e", "observability:e")
        green = supervisor.EngineHealth("FACT-001", True, True, True, True, True, company_id="fenix", environment="PROD", evidence_refs=evidence, version="2.0.0")
        blank_version = supervisor.EngineHealth("FACT-001", True, True, True, True, True, company_id="fenix", environment="PROD", evidence_refs=evidence, version="")
        self.assertEqual(red.state, supervisor.RED)
        self.assertEqual(green.state, supervisor.GREEN)
        self.assertEqual(blank_version.state, supervisor.RED)

    def test_supervisor_human_required_preempts_green(self):
        health = supervisor.EngineHealth("FACT-001", True, True, True, True, True, True)
        self.assertEqual(health.state, supervisor.HUMAN_REQUIRED)

if __name__ == "__main__":
    unittest.main()
