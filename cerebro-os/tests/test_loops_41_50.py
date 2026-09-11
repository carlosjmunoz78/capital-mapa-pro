import importlib.util
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


cp = load("core_control_plane_41_50", "core/control_plane.py")


class Loops41To50Tests(unittest.TestCase):
    def test_loop41_core_state_is_company_scoped_and_provenanced(self):
        store = cp.CoreState()
        store.put(cp.CoreValue("fenix", "priority", "cash", "1.0.0", "src:master"))
        self.assertEqual("cash", store.get("fenix", "priority").value)
        self.assertIsNone(store.get("other", "priority"))

    def test_loop42_orchestrator_orders_by_dependencies_and_priority(self):
        orch = cp.Orchestrator("fenix")
        orch.add(cp.OrchestratedTask("a", "fenix", 10))
        orch.add(cp.OrchestratedTask("b", "fenix", 100, ("a",)))
        orch.add(cp.OrchestratedTask("c", "fenix", 50))
        self.assertEqual(("c", "a"), orch.ready())
        orch.attempt("a", True)
        self.assertEqual(("b", "c"), orch.ready())
        with self.assertRaises(ValueError):
            orch.add(cp.OrchestratedTask("x", "other", 1))

    def test_loop43_hex_accepts_only_canonical_reasons(self):
        q = cp.HumanExceptionQueue("fenix")
        q.emit(cp.HumanException("fenix", "LEG-001", "LEGAL_REQUIRED", "e:1", 90))
        self.assertEqual("LEGAL_REQUIRED", q.pending()[0].reason)
        with self.assertRaises(ValueError):
            q.emit(cp.HumanException("fenix", "X", "MISSING_CREDENTIAL", "e:2"))

    def test_loop44_decision_is_deterministic_and_explainable(self):
        weights = {"benefit": 1, "cost": 1, "urgency": 1, "risk": 1, "speed": 1}
        ranked = cp.rank_options((
            cp.DecisionOption("a", 10, 2, 5, 1, 3),
            cp.DecisionOption("b", 8, 1, 2, 1, 1),
        ), weights)
        self.assertEqual("a", ranked[0].option_id)
        self.assertTrue(ranked[0].explanation)

    def test_loop45_semantic_catalog_rejects_duplicates(self):
        cat = cp.SemanticCatalog()
        cat.register(cp.SemanticEntity("Expediente", ("id", "status")))
        self.assertEqual("Expediente", cat.resolve("expediente").name)
        with self.assertRaises(ValueError):
            cat.register(cp.SemanticEntity("EXPEDIENTE", ("id",)))

    def test_loop46_ownership_requires_owner_approver_backup(self):
        reg = cp.OwnershipRegistry()
        reg.set(cp.Ownership("FACT-001", "tech", "gov", "backup"))
        self.assertEqual("tech", reg.get("FACT-001").owner)
        with self.assertRaises(ValueError):
            reg.set(cp.Ownership("X", "", "gov", "backup"))

    def test_loop47_objectives_support_at_least_and_at_most(self):
        self.assertEqual("GREEN", cp.Objective("o1", "sales", 10, 12).status())
        self.assertEqual("GREEN", cp.Objective("o2", "cost", 10, 8, "AT_MOST").status())
        self.assertEqual("RED", cp.Objective("o3", "cost", 10, 12, "AT_MOST").status())

    def test_loop48_adr_is_append_only_and_has_rollback(self):
        log = cp.ADRLog()
        adr = cp.ArchitectureDecision("ADR-1", "context", "choice", ("alt",), "effects", "rollback")
        log.append(adr)
        self.assertEqual(1, len(log.entries()))
        with self.assertRaises(ValueError):
            log.append(adr)

    def test_loop49_config_rejects_secrets(self):
        cfg = cp.MasterConfig()
        cfg.set(cp.ConfigValue("worker.batch_size", "10", "LAB", "1.0.0"))
        self.assertEqual("10", cfg.get("LAB", "worker.batch_size").value)
        with self.assertRaises(ValueError):
            cfg.set(cp.ConfigValue("api_token", "value", "LAB", "1.0.0"))

    def test_loop50_semver_compatibility_rejects_breaking_major(self):
        self.assertTrue(cp.compatible("1.3.0", "1.2.0"))
        self.assertFalse(cp.compatible("2.0.0", "1.2.0"))
        with self.assertRaises(ValueError):
            cp.parse_semver("1.2")


if __name__ == "__main__":
    unittest.main()
