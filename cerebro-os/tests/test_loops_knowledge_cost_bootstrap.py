import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

knowledge = load("knowledge_pipeline_loop", "knowledge/pipeline.py")
zero_cost = load("zero_cost_loop", "routing/zero_cost.py")
bootstrap = load("bootstrap_orchestrator_loop", "multicompany/bootstrap_orchestrator.py")
canonical = load("canonical_loader_loop", "registry/canonical_loader.py")


class GroupedNextLoops(unittest.TestCase):
    def test_loop_knowledge_is_tenant_scoped_and_requires_provenance(self):
        idx = knowledge.KnowledgeIndex()
        item = knowledge.KnowledgeItem(
            company_id="fenix-capital",
            source_id="source-1",
            source_type="OFFICIAL",
            content_ref="doc://master/1",
            version="1.0.0",
            observed_at="2026-09-11T18:00:00Z",
            provenance_ref="sha256://abc",
        )
        idx.upsert(item)
        self.assertEqual(item, idx.get("fenix-capital", "source-1"))
        self.assertIsNone(idx.get("other-company", "source-1"))
        self.assertFalse(item.is_stale(7200, datetime(2026, 9, 11, 19, 0, tzinfo=timezone.utc)))
        with self.assertRaises(ValueError):
            knowledge.KnowledgeItem("fenix", "x", "OFFICIAL", "ref", "1", "2026-09-11T18:00:00Z", "").validate()

    def test_loop_zero_cost_prefers_deterministic_and_offloads_heavy_work(self):
        decision = zero_cost.choose_route((
            zero_cost.ExecutionOption("PAID", True, 1.0),
            zero_cost.ExecutionOption("FREE_TIER", True, 0.0),
            zero_cost.ExecutionOption("DETERMINISTIC", True, 0.0),
        ), "TRAINING")
        self.assertTrue(decision.allowed)
        self.assertEqual("DETERMINISTIC", decision.route_type)
        self.assertTrue(decision.offload_from_supabase)
        blocked = zero_cost.choose_route((zero_cost.ExecutionOption("PAID", True, 0.5),), "STANDARD")
        self.assertFalse(blocked.allowed)
        self.assertEqual("MONEY_LIMIT", blocked.reason)

    def test_loop_bootstrap_retries_failed_phase_and_preserves_canonical_order(self):
        ids = set(canonical.canonical_engine_ids())
        state = bootstrap.BootstrapState("fenix-capital", ("COMP-REG-001", "KBOOT-001"), environment="LAB", version="2.0.0")
        state.validate(ids)
        self.assertEqual("company_registry", state.next_phase())
        failed = bootstrap.advance(state, "company_registry", False)
        self.assertEqual("company_registry", failed.next_phase())
        with self.assertRaises(ValueError):
            bootstrap.advance(failed, "company_registry", True)
        recovered = bootstrap.advance(failed, "company_registry", True, evidence_ref="evidence:company_registry", version="2.0.0")
        self.assertEqual(("company_registry",), recovered.completed_phases)
        self.assertEqual("business_discovery", recovered.next_phase())
        self.assertEqual("evidence:company_registry", dict(recovered.evidence_by_phase)["company_registry"])
        recovered.validate(ids)
        with self.assertRaises(ValueError):
            bootstrap.BootstrapState("fenix", ("NOT-A-CANONICAL-ID",)).validate(ids)


if __name__ == "__main__":
    unittest.main()
