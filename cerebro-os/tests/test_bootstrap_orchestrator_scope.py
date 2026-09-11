import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bootstrap_orchestrator_scope", ROOT / "multicompany/bootstrap_orchestrator.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["bootstrap_orchestrator_scope"] = mod
spec.loader.exec_module(mod)


class BootstrapOrchestratorScopeTests(unittest.TestCase):
    def test_success_requires_evidence_and_exact_scope(self):
        state = mod.BootstrapState("fenix", ("FACT-001",), environment="PROD", version="2.0.0")
        with self.assertRaises(ValueError):
            mod.advance(state, "company_registry", True)
        with self.assertRaises(ValueError):
            mod.advance(state, "company_registry", True, evidence_ref="e", version="1.0.0")
        next_state = mod.advance(state, "company_registry", True, evidence_ref="e:registry", company_id="fenix", environment="PROD", version="2.0.0")
        self.assertEqual(("company_registry",), next_state.completed_phases)
        self.assertEqual("business_discovery", next_state.next_phase())

    def test_health_gate_needs_evidence_for_every_phase(self):
        state = mod.BootstrapState("fenix", ("FACT-001",), environment="LAB", version="2.0.0")
        for phase in mod.CANONICAL_PHASES:
            state = mod.advance(state, phase, True, evidence_ref=f"e:{phase}", version="2.0.0")
        self.assertTrue(state.ready_for_health_gate)
        self.assertIsNone(state.next_phase())


if __name__ == "__main__":
    unittest.main()
