import importlib.util
import json
import sys
import tempfile
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


canonical = load("three_canonical", "registry/canonical_loader.py")
bootstrap = load("three_bootstrap", "registry/bootstrap_groups.py")
closure = load("three_closure", "governance/dependency_closure.py")
promotion = load("three_promotion", "governance/promotion_gate.py")
control = load("three_control", "gateway/control_plane.py")
onboarding = load("three_onboarding", "onboarding/executor.py")
bundle = load("three_bundle", "resilience/company_bundle.py")

CONTROL_EVIDENCE = {
    "route": "evidence:route",
    "policy": "evidence:policy",
    "supervisor": "evidence:supervisor",
    "tribunal": "evidence:tribunal",
    "promotion": "evidence:promotion",
}


class ThreeGroupedLoopsTests(unittest.TestCase):
    def test_loop1_bootstrap_groups_are_canonical_and_unique(self):
        ids = canonical.canonical_engine_ids()
        result = bootstrap.validate_bootstrap_groups(ids)
        self.assertTrue(result["valid"])
        self.assertEqual((), result["missing"])
        self.assertEqual((), result["duplicates"])
        self.assertEqual("FACTORY_REGISTRY", bootstrap.group_for("FACT-001"))
        self.assertEqual("CONSOLE", bootstrap.group_for("CONSOLE-001"))

    def test_loop1_dependency_closure_rejects_unknown_and_cycles(self):
        ids = canonical.canonical_engine_ids()
        graph = closure.DependencyClosure(ids)
        graph.add("GOV-001", ())
        graph.add("FACT-001", ("GOV-001",))
        graph.add("RUNTIME-001", ("FACT-001", "GOV-001"))
        order = graph.order()
        self.assertLess(order.index("GOV-001"), order.index("FACT-001"))
        self.assertLess(order.index("FACT-001"), order.index("RUNTIME-001"))
        with self.assertRaises(ValueError):
            graph.add("NOT-CANONICAL", ())
        with self.assertRaises(ValueError):
            graph.add("GOV-001", ("RUNTIME-001",))

    def test_loop2_promotion_gate_requires_every_gate(self):
        gates = promotion.all_green_gates()
        green = promotion.decide_promotion(engine_id="FACT-001", environment="LAB", gates=gates)
        self.assertEqual("LAB_GREEN", green["decision"])
        gates["rollback"] = False
        red = promotion.decide_promotion(engine_id="FACT-001", environment="LAB", gates=gates)
        self.assertEqual("BLOCKED", red["decision"])
        self.assertIn("rollback", red["missing"])
        human = promotion.decide_promotion(engine_id="FACT-001", environment="LAB", gates=promotion.all_green_gates(), human_required=True)
        self.assertEqual("HUMAN_REQUIRED", human["decision"])

    def test_loop2_control_plane_requires_route_supervisor_tribunal_promotion_and_evidence(self):
        without_evidence = control.control_decision(
            route_status="ROUTED",
            policy_decision="ALLOW",
            supervisor_state="GREEN",
            tribunal_approved=True,
            promotion_decision="LAB_GREEN",
        )
        self.assertEqual("BLOCKED", without_evidence["status"])
        self.assertEqual("EVIDENCE_MISSING", without_evidence["reason"])

        green = control.control_decision(
            route_status="ROUTED",
            policy_decision="ALLOW",
            supervisor_state="GREEN",
            tribunal_approved=True,
            promotion_decision="LAB_GREEN",
            evidence_refs=CONTROL_EVIDENCE,
        )
        self.assertEqual("ALLOW_EXECUTION", green["status"])
        red = control.control_decision(
            route_status="ROUTED",
            policy_decision="ALLOW",
            supervisor_state="RED",
            tribunal_approved=True,
            promotion_decision="LAB_GREEN",
        )
        self.assertEqual("BLOCKED", red["status"])
        human = control.control_decision(
            route_status="NO_ROUTE",
            policy_decision="ALLOW",
            supervisor_state="GREEN",
            tribunal_approved=True,
            promotion_decision="LAB_GREEN",
        )
        self.assertEqual({"status": "HUMAN_REQUIRED", "reason": "LOW_CONFIDENCE"}, human)
        control.validate_human_reason("LOW_CONFIDENCE")
        with self.assertRaises(ValueError):
            control.validate_human_reason("RANDOM_REASON")

    def test_loop3_onboarding_red_retry_then_full_green(self):
        executor = onboarding.OnboardingExecutor("fenix-capital")
        first = executor.next_phase()
        executor.mark_red(first, "temporary scanner error")
        self.assertEqual("RED", executor.state)
        executor.retry(first)
        self.assertEqual("IN_PROGRESS", executor.state)
        while executor.next_phase() is not None:
            phase = executor.next_phase()
            executor.mark_green(phase, evidence_refs=(f"evidence:{phase}",))
        self.assertEqual("GREEN", executor.state)
        self.assertEqual(len(onboarding.CANONICAL_PHASES), len(executor.completed))

    def test_loop3_company_backup_bundle_detects_tampering(self):
        files = {
            "registry/company.json": b'{"company_id":"fenix-capital"}',
            "config/runtime.json": b'{"environment":"LAB"}',
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = bundle.write_bundle(root, "fenix-capital", files)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertTrue(bundle.verify_bundle(root, manifest))
            (root / "fenix-capital" / "config" / "runtime.json").write_bytes(b"tampered")
            self.assertFalse(bundle.verify_bundle(root, manifest))


if __name__ == "__main__":
    unittest.main()
