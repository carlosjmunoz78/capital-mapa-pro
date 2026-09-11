import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


canonical = load("l46_canonical", "registry/canonical_loader.py")
planner_mod = load("l46_planner", "multicompany/capability_planner.py")
health_mod = load("l46_health", "multicompany/health.py")
deps_mod = load("l46_deps", "multicompany/dependency_readiness.py")
backup_mod = load("l46_backup", "multicompany/backup_gate.py")
pipeline_mod = load("l46_pipeline", "console/pipeline.py")


class LoopsFourToSixTests(unittest.TestCase):
    def test_loop4_capability_activation_is_deterministic_and_canonical(self):
        ids = canonical.canonical_engine_ids()
        planner = planner_mod.CapabilityActivationPlanner(ids)
        planner.add_rule(
            name="base_company",
            predicate=lambda profile: bool(profile.get("authorized")),
            required=("COMP-REG-001", "TENANT-001", "SUP-001", "COMP-BKP-001"),
            optional=("CONSOLE-001",),
        )
        planner.add_rule(
            name="digital_presence",
            predicate=lambda profile: profile.get("has_web") is True,
            required=("SCAN-001", "WAUD-001", "KW-001"),
            optional=("SEO-001", "SOCAUD-001"),
        )
        plan = planner.plan({"authorized": True, "has_web": True})
        self.assertIn("COMP-REG-001", plan["required"])
        self.assertIn("SCAN-001", plan["required"])
        self.assertIn("CONSOLE-001", plan["optional"])
        with self.assertRaises(ValueError):
            planner.add_rule(name="bad", predicate=lambda profile: True, required=("NOT-AN-ENGINE",))

    def test_loop5_company_health_requires_every_required_engine_green(self):
        result = health_mod.company_health(
            company_id="fenix-capital",
            required_engines=("COMP-REG-001", "TENANT-001", "SUP-001"),
            engine_states={"COMP-REG-001": "GREEN", "TENANT-001": "GREEN", "SUP-001": "RED"},
            evidence_refs={"COMP-REG-001": ("e1",), "TENANT-001": ("e2",)},
        )
        self.assertEqual("RED", result["state"])
        self.assertEqual(("SUP-001",), result["not_green"])
        green = health_mod.company_health(
            company_id="fenix-capital",
            required_engines=("COMP-REG-001", "TENANT-001"),
            engine_states={"COMP-REG-001": "GREEN", "TENANT-001": "GREEN"},
            evidence_refs={"COMP-REG-001": ("e1",), "TENANT-001": ("e2",)},
        )
        self.assertEqual("GREEN", green["state"])
        no_evidence = health_mod.company_health(
            company_id="fenix-capital",
            required_engines=("COMP-REG-001",),
            engine_states={"COMP-REG-001": "GREEN"},
        )
        self.assertEqual("RED", no_evidence["state"])
        self.assertEqual(("COMP-REG-001",), no_evidence["green_without_evidence"])

    def test_loop5_dependency_and_backup_readiness(self):
        canonical_ids = set(canonical.canonical_engine_ids())
        dependencies = {"RUNTIME-001": ("FACT-001", "GOV-001"), "EVT-001": ("RUNTIME-001",)}
        deps_mod.validate_dependency_ids(canonical_ids=canonical_ids, dependencies=dependencies)
        red = deps_mod.dependency_readiness(active_engines={"RUNTIME-001", "FACT-001"}, dependencies=dependencies)
        self.assertFalse(red["ready"])
        self.assertIn("GOV-001", red["missing_dependencies"]["RUNTIME-001"])
        green = deps_mod.dependency_readiness(active_engines={"GOV-001", "FACT-001", "RUNTIME-001", "EVT-001"}, dependencies=dependencies)
        self.assertTrue(green["ready"])
        blocked = backup_mod.backup_gate(company_id="fenix-capital", backup_verified=True, restore_verified=True, rebuild_verified=False, rollback_verified=True)
        self.assertFalse(blocked["ready"])
        evidence = {name: f"test-evidence:{name}" for name in backup_mod.CHECKS}
        ready = backup_mod.backup_gate(company_id="fenix-capital", backup_verified=True, restore_verified=True, rebuild_verified=True, rollback_verified=True, evidence_refs=evidence)
        self.assertTrue(ready["ready"])

    def test_loop6_console_pipeline_only_routes_through_gateway_and_audits(self):
        audits = []
        def gateway_route(command):
            return {"status": "ROUTED", "engine_id": "SUP-001", "company_id": command["company_id"]}
        pipeline = pipeline_mod.ConsolePipeline(gateway_route, audits.append)
        command = {
            "request_id": "req-1",
            "user_id": "user-1",
            "company_id": "fenix-capital",
            "context_type": "company",
            "message": "status",
        }
        result = pipeline.execute(command)
        self.assertEqual("ROUTED", result["status"])
        self.assertEqual(("CONSOLE", "GATEWAY", "POLICY", "ENGINE", "AUDIT"), result["path"])
        self.assertEqual("fenix-capital", audits[0]["company_id"])
        self.assertEqual("ROUTED", audits[0]["gateway_status"])
        with self.assertRaises(ValueError):
            pipeline.execute({"request_id": "req-2"})


if __name__ == "__main__":
    unittest.main()
