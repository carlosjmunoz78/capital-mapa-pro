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

r = load("resilience_control_55_67", "resilience/control_engines.py")

class Loops55To67Tests(unittest.TestCase):
    def test_loop55_simulation_applies_deltas_without_mutating_baseline(self):
        baseline = {"cash": 100.0}
        result = r.simulate(baseline, r.Scenario("s1", (("cash", -20.0), ("sales", 5.0))))
        self.assertEqual({"cash": 80.0, "sales": 5.0}, result)
        self.assertEqual({"cash": 100.0}, baseline)

    def test_loop56_twin_snapshot_is_versioned_and_deterministic(self):
        a = r.TwinSnapshot("fenix", "1.0.0", (("x", "1"), ("y", "2")))
        b = r.TwinSnapshot("fenix", "1.0.0", (("y", "2"), ("x", "1")))
        self.assertEqual(a.digest, b.digest)

    def test_loop57_incident_security_escalates(self):
        incident = r.Incident("i1", "fenix", "SECURITY", "HIGH", "e:1")
        incident.validate()
        self.assertEqual("SECURITY_INCIDENT", incident.human_reason)

    def test_loop58_self_repair_requires_reversible_precheck_and_rollback(self):
        ok = r.RepairAction("a", True, True, True, "rb:1")
        self.assertTrue(ok.allowed)
        self.assertEqual("GREEN", ok.result)
        bad = r.RepairAction("a", False, True, True, "rb:1")
        self.assertEqual("BLOCKED", bad.result)

    def test_loop59_security_enforces_scopes_and_high_risk_review(self):
        self.assertEqual("ALLOW", r.security_decision(r.SecurityRequest("fenix", frozenset({"read"}), frozenset({"read"}))))
        self.assertEqual("DENY", r.security_decision(r.SecurityRequest("fenix", frozenset(), frozenset({"read"}))))
        self.assertEqual("HUMAN_REQUIRED", r.security_decision(r.SecurityRequest("fenix", frozenset({"write"}), frozenset({"write"}), True)))

    def test_loop60_iam_is_company_environment_and_permission_scoped(self):
        grant = r.IdentityGrant("id1", "fenix", "DOC-001", frozenset({"document.read"}), "LAB")
        self.assertTrue(grant.allows("document.read", "fenix", "LAB"))
        self.assertFalse(grant.allows("document.read", "other", "LAB"))
        self.assertFalse(grant.allows("document.write", "fenix", "LAB"))

    def test_loop61_secret_reference_rejects_embedded_values(self):
        r.SecretReference("ENV", "CEREBRO_API_TOKEN").validate()
        with self.assertRaises(ValueError):
            r.SecretReference("ENV", "token=abc").validate()

    def test_loop62_red_team_compares_expected_and_actual_decision(self):
        self.assertTrue(r.RedTeamCase("rt1", "DENY", "DENY", "e").passed)
        self.assertFalse(r.RedTeamCase("rt2", "DENY", "ALLOW", "e").passed)

    def test_loop63_software_qa_requires_all_test_classes_and_evidence(self):
        self.assertTrue(r.SoftwareQualityGate(True, True, True, True, "ci:1").green)
        self.assertFalse(r.SoftwareQualityGate(True, True, False, True, "ci:1").green)

    def test_loop64_process_qa_requires_all_checks(self):
        gate = r.ProcessQualityGate("p", ("a", "b"), frozenset({"a", "b"}), "e")
        self.assertTrue(gate.green)
        self.assertFalse(r.ProcessQualityGate("p", ("a", "b"), frozenset({"a"}), "e").green)

    def test_loop65_regression_requires_approval_on_behavior_or_contract_change(self):
        old = r.RegressionBaseline("c1", "b1")
        self.assertEqual("GREEN", r.regression_status(old, old))
        self.assertEqual("RED", r.regression_status(old, r.RegressionBaseline("c1", "b2")))
        self.assertEqual("GREEN", r.regression_status(old, r.RegressionBaseline("c1", "b2"), True))

    def test_loop66_continuity_requires_backup_restore_rebuild_alternate_runtime_runbook(self):
        ready = r.ContinuityReadiness(True, True, True, True, "runbook:1")
        self.assertTrue(ready.green)
        self.assertFalse(r.ContinuityReadiness(True, False, True, True, "runbook:1").green)

    def test_loop67_crisis_high_risk_requires_human(self):
        self.assertEqual(("HUMAN_REQUIRED", "HIGH_RISK"), r.CrisisAssessment("fenix", "HIGH", "company", "e").decision())
        self.assertEqual(("GREEN", None), r.CrisisAssessment("fenix", "LOW", "team", "e").decision())

if __name__ == "__main__":
    unittest.main()
