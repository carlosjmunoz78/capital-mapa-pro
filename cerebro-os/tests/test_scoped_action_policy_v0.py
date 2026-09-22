import importlib.util
from pathlib import Path
import sys
import unittest

SRC = Path(__file__).resolve().parents[1] / "identity" / "scoped_action_policy_v0.py"
spec = importlib.util.spec_from_file_location("scoped_action_policy_v0", SRC)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ScopedActionPolicyTests(unittest.TestCase):
    def req(self, **changes):
        values = dict(company_id="fenix", engine_id="OPERATOR-001",
            environment="LAB", version="v0", action_id="test-001",
            action_class=module.ActionClass.DRAFT, target_origin="https://example.com/",
            approved_origins=("https://example.com/",), connector_available=False,
            identity_scoped=True, policy_green=True, backup_verified=True,
            rollback_verified=True, preprod_green=True, budget_eur=0,
            budget_limit_eur=0)
        values.update(changes)
        return module.ScopedAction(**values)

    def test_draft_never_becomes_executable_without_bounded_runtime(self):
        p = module.evaluate_action(self.req())
        self.assertEqual(p["decision"], "BLOCKED")
        self.assertFalse(p["external_write_permitted"])
        self.assertIn("EXTERNAL_WRITE_RUNTIME_NOT_IMPLEMENTED", p["blockers"])

    def test_legal_signature_money_and_security_are_human_exceptions(self):
        for change, expected in (
            (dict(action_class=module.ActionClass.LEGAL), "LEGAL_REQUIRED"),
            (dict(action_class=module.ActionClass.SIGNATURE), "SIGNATURE_REQUIRED"),
            (dict(action_class=module.ActionClass.PURCHASE), "HIGH_RISK"),
            (dict(security_incident=True), "SECURITY_INCIDENT"),
            (dict(budget_eur=1), "MONEY_LIMIT"),
            (dict(customer_requests_human=True), "CUSTOMER_HUMAN_REQUEST"),
            (dict(low_confidence=True), "LOW_CONFIDENCE"),
            (dict(policy_green=False), "POLICY_CONFLICT"),
        ):
            with self.subTest(change=change):
                p = module.evaluate_action(self.req(**change))
                self.assertEqual(p["decision"], "HUMAN_REQUIRED")
                self.assertIn(expected, p["human_reasons"])

    def test_connector_scope_publication_and_backup_blockers(self):
        p = module.evaluate_action(self.req(
            action_class=module.ActionClass.EXTERNAL_PUBLISH,
            connector_available=True, identity_scoped=False,
            target_origin="https://example.com.evil/",
            backup_verified=False, rollback_verified=False,
            preprod_green=False, external_publication_approved=False))
        for reason in ("CONNECTOR_FIRST", "IDENTITY_SCOPE_MISSING",
                       "TARGET_ORIGIN_NOT_APPROVED", "PUBLISH_POLICY_APPROVAL_MISSING",
                       "MUTATION_RELEASE_GATES_MISSING"):
            self.assertIn(reason, p["blockers"])

    def test_authorized_read_is_a_plan_not_browser_command(self):
        p = module.evaluate_action(self.req(action_class=module.ActionClass.READ))
        self.assertEqual(p["decision"], "POLICY_GREEN_NOT_EXECUTED")
        self.assertFalse(p["runtime_dispatch_permitted"])


if __name__ == "__main__":
    unittest.main()
