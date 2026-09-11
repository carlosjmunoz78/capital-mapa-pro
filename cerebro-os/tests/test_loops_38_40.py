import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


coh = load("coh_loop38", "mortgage/coherence.py")
via = load("via_loop39", "mortgage/viability.py")
mortgage = load("mortgage_loop23_extended", "mortgage/pipeline.py")
commercial = load("commercial_coverage", "commercial/pipeline.py")
enterprise = load("enterprise_coverage", "enterprise/ops.py")
growth = load("growth_coverage", "growth/bootstrap.py")
families = load("families_coverage", "processes/families.py")
platform = load("platform_coverage", "processes/platform_loops_28_37.py")
coverage = load("coverage_loop40", "registry/controller_coverage.py")


class Loops38To40Tests(unittest.TestCase):
    def test_loop38_coherence_detects_contradictions_and_is_tenant_scoped(self):
        graph = coh.CoherenceGraph("fenix")
        graph.add(coh.Fact("fenix", "exp-1", "employment_status", "indefinido", "doc:nomina", 0.99))
        graph.add(coh.Fact("fenix", "exp-1", "employment_status", "indefinido", "doc:vida-laboral", 0.98))
        self.assertEqual("GREEN", graph.status())
        graph.add(coh.Fact("fenix", "exp-1", "employment_status", "temporal", "doc:contrato", 0.95))
        self.assertEqual("RED", graph.status())
        self.assertEqual(1, len(graph.contradictions()))
        with self.assertRaises(ValueError):
            graph.add(coh.Fact("other", "exp-1", "employment_status", "temporal", "doc:x", 1.0))

    def test_loop38_low_confidence_emits_human_required(self):
        graph = coh.CoherenceGraph("fenix", min_confidence=0.75)
        graph.add(coh.Fact("fenix", "exp-1", "income", "2000", "doc:ocr", 0.40))
        self.assertEqual("HUMAN_REQUIRED", graph.status())

    def test_loop39_viability_is_versioned_explainable_and_has_no_embedded_thresholds(self):
        rules = (
            via.ViabilityRule("r1", "ratio", "<=", 0.35, 1.0, True, "2026.09", "ratio within authorized rule"),
            via.ViabilityRule("r2", "savings", ">=", 10000, 1.0, False, "2026.09", "savings within authorized rule"),
        )
        engine = via.ViabilityEvaluator("fenix", rules)
        result = engine.evaluate("fenix", {"ratio": 0.30, "savings": 12000})
        self.assertEqual("GREEN", result.status)
        self.assertEqual("2026.09", result.rules_version)
        self.assertEqual(1.0, result.confidence)
        self.assertTrue(result.explanations)
        low = engine.evaluate("fenix", {"ratio": 0.30})
        self.assertEqual("HUMAN_REQUIRED", low.status)
        failed = engine.evaluate("fenix", {"ratio": 0.50, "savings": 12000})
        self.assertEqual("RED", failed.status)
        with self.assertRaises(ValueError):
            engine.evaluate("other", {"ratio": 0.30, "savings": 12000})

    def test_loop39_rejects_mixed_rule_versions(self):
        with self.assertRaises(ValueError):
            via.ViabilityEvaluator("fenix", (
                via.ViabilityRule("a", "x", ">=", 1, 1, False, "v1", "a"),
                via.ViabilityRule("b", "y", ">=", 1, 1, False, "v2", "b"),
            ))

    def test_loop23_now_connects_coh_and_via_in_canonical_position(self):
        self.assertLess(mortgage.MORTGAGE_SEQUENCE.index("AML-001"), mortgage.MORTGAGE_SEQUENCE.index("COH-001"))
        self.assertLess(mortgage.MORTGAGE_SEQUENCE.index("COH-001"), mortgage.MORTGAGE_SEQUENCE.index("VIA-001"))
        self.assertLess(mortgage.MORTGAGE_SEQUENCE.index("VIA-001"), mortgage.MORTGAGE_SEQUENCE.index("BNK-001"))

    def test_loop40_controller_coverage_is_exactly_177_of_177(self):
        canonical = json.loads((ROOT / "registry/canonical_177.json").read_text(encoding="utf-8"))["engine_ids"]
        groups = {
            **platform.LOOPS_28_37,
            **{f"family:{k}": v for k, v in families.PROCESS_FAMILIES.items()},
            "commercial": commercial.COMMERCIAL_SEQUENCE,
            "mortgage": mortgage.MORTGAGE_SEQUENCE,
            "enterprise": enterprise.ENTERPRISE_SEQUENCE,
            "growth_bootstrap": growth.CANONICAL_GROWTH_SEQUENCE,
        }
        report = coverage.audit_controller_coverage(canonical, groups)
        self.assertEqual(177, report.canonical_count)
        self.assertEqual(177, report.covered_count)
        self.assertEqual((), report.missing)
        self.assertEqual((), report.unknown)
        self.assertEqual("GREEN", report.status)


if __name__ == "__main__":
    unittest.main()
