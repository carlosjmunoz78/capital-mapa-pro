import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


knowledge = load("knowledge_retrieval_loop19", "knowledge/retrieval.py")
discovery = load("discovery_pipeline_loop20", "discovery/pipeline.py")
growth = load("growth_bootstrap_loop21", "growth/bootstrap.py")


class Loop19KnowledgeTests(unittest.TestCase):
    def test_retrieval_is_tenant_scoped_cached_and_invalidated_on_update(self):
        idx = knowledge.KnowledgeIndex()
        idx.upsert(knowledge.KnowledgeRecord("c1", "r1", "hipoteca fija euribor", "src:1", "2026-09-10T00:00:00+00:00"))
        idx.upsert(knowledge.KnowledgeRecord("c2", "r2", "hipoteca fija otra empresa", "src:2", "2026-09-10T00:00:00+00:00"))
        self.assertEqual(("r1",), idx.retrieve("c1", "hipoteca fija"))
        idx.upsert(knowledge.KnowledgeRecord("c1", "r1", "hipoteca variable euribor", "src:1", "2026-09-11T00:00:00+00:00", "1.0.1"))
        self.assertEqual((), idx.retrieve("c1", "hipoteca fija"))
        self.assertEqual(("r1",), idx.retrieve("c1", "hipoteca variable"))

    def test_freshness_flags_old_records(self):
        idx = knowledge.KnowledgeIndex()
        idx.upsert(knowledge.KnowledgeRecord("c1", "old", "dato", "src", "2026-09-01T00:00:00+00:00"))
        now = datetime(2026, 9, 11, tzinfo=timezone.utc)
        self.assertEqual(("old",), idx.stale("c1", 24 * 3600, now=now))


class Loop20DiscoveryTests(unittest.TestCase):
    def test_discovery_denies_cross_company_and_requires_evidence_confidence(self):
        run = discovery.DiscoveryRun("fenix")
        run.add(discovery.DiscoveryFinding("fenix", "SCAN-001", "fenixcapital.es", "evidence:web:1", 0.95))
        self.assertEqual("GREEN", run.engine_status("SCAN-001"))
        run.add(discovery.DiscoveryFinding("fenix", "KW-001", "hipotecas", "evidence:kw:1", 0.40))
        self.assertEqual("HUMAN_REQUIRED", run.engine_status("KW-001"))
        with self.assertRaises(ValueError):
            run.add(discovery.DiscoveryFinding("other", "WAUD-001", "site", "evidence:web:2", 0.99))


class Loop21GrowthTests(unittest.TestCase):
    def test_bootstrap_is_ordered_and_green_requires_evidence(self):
        boot = growth.GrowthBootstrap("fenix")
        self.assertEqual("SEOBOOT-001", boot.next_engine())
        self.assertFalse(boot.can_advance("SOCBOOT-001"))
        with self.assertRaises(ValueError):
            boot.update(growth.BootstrapStep("fenix", "SEOBOOT-001", "GREEN"))
        for engine_id in growth.CANONICAL_GROWTH_SEQUENCE:
            self.assertTrue(boot.can_advance(engine_id))
            boot.update(growth.BootstrapStep("fenix", engine_id, "GREEN", f"evidence:{engine_id}"))
        self.assertIsNone(boot.next_engine())
        self.assertEqual("GREEN", boot.system_status())

    def test_bootstrap_red_stays_on_same_engine(self):
        boot = growth.GrowthBootstrap("fenix")
        boot.update(growth.BootstrapStep("fenix", "SEOBOOT-001", "RED"))
        self.assertEqual("SEOBOOT-001", boot.next_engine())
        self.assertEqual("RED", boot.system_status())

    def test_bootstrap_rejects_cross_environment_or_version(self):
        boot = growth.GrowthBootstrap("fenix", "PROD", "2.0.0")
        with self.assertRaises(ValueError):
            boot.update(growth.BootstrapStep("fenix", "SEOBOOT-001", "GREEN", "e", "LAB", "2.0.0"))
        with self.assertRaises(ValueError):
            boot.update(growth.BootstrapStep("fenix", "SEOBOOT-001", "GREEN", "e", "PROD", "1.0.0"))
        boot.update(growth.BootstrapStep("fenix", "SEOBOOT-001", "GREEN", "e:prod", "PROD", "2.0.0"))
        self.assertEqual("SOCBOOT-001", boot.next_engine())


if __name__ == "__main__":
    unittest.main()
