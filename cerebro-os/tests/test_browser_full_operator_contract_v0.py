import importlib.util
import pathlib
import sys
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / "identity" / "browser_full_operator_contract_v0.py"
spec = importlib.util.spec_from_file_location("full_operator_contract", PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class FullOperatorContractTests(unittest.TestCase):
    def request(self, **kw):
        args = dict(
            company_id="fenix", engine_id="ACCESSBOOT-001", environment="LAB",
            version="v0", device_id="test-device", profile_id="Default",
            origin="https://example.com/", action="READ_PAGE", target_ref="test-target",
            idempotency_key="test-once", audit_ref="test-audit",
            approved_origins=("https://example.com/",), connector_available=False,
            browser_fresh=True, policy_green=True, kill_switch_enabled=True,
            audit_available=True, data_contract_green=True, snapshot_available=True,
            rollback_tested=True, preprod_old_new_green=True,
        )
        args.update(kw)
        return module.OperatorRequest(**args)

    def plan(self, req, implemented=frozenset()):
        return module.plan_operator_action(req, implemented_actions=implemented)

    def test_no_new_executor_is_silently_enabled(self):
        for action in module.SUPPORTED_ACTIONS:
            with self.subTest(action=action):
                result = self.plan(self.request(action=action, action_approved=True))
                self.assertFalse(result["dispatch_allowed"])
                self.assertIn("EXECUTOR_NOT_IMPLEMENTED", result["blockers"])

    def test_scoped_read_can_proceed_only_with_implemented_executor(self):
        result = self.plan(self.request(), frozenset({"READ_PAGE"}))
        self.assertEqual(result["status"], "GREEN")
        self.assertTrue(result["dispatch_allowed"])
        self.assertFalse(result["prod_activation_allowed"])
        self.assertFalse(result["credential_value_exposure_allowed"])

    def test_write_requires_explicit_scope_and_release_gates(self):
        result = self.plan(self.request(action="SUBMIT_FORM"),
                           frozenset({"SUBMIT_FORM"}))
        self.assertEqual(result["status"], "HUMAN_REQUIRED")
        self.assertIn("WRITE_ACTION_APPROVAL_REQUIRED", result["blockers"])
        result = self.plan(
            self.request(action="SUBMIT_FORM", action_approved=True,
                         rollback_tested=False), frozenset({"SUBMIT_FORM"}))
        self.assertIn("MUTATION_RELEASE_GATES_REQUIRED", result["blockers"])
        self.assertFalse(result["dispatch_allowed"])

    def test_block_prod_cross_company_unapproved_origin_and_connector(self):
        result = self.plan(self.request(company_id="other", environment="PROD",
            origin="https://bad.example/", connector_available=True),
            frozenset({"READ_PAGE"}))
        self.assertFalse(result["dispatch_allowed"])
        self.assertIn("LAB_FIRST_SCOPE_REQUIRED", result["blockers"])
        self.assertIn("ORIGIN_APPROVAL_REQUIRED", result["blockers"])
        self.assertIn("CONNECTOR_FIRST", result["blockers"])

    def test_high_risk_actions_stay_human_required(self):
        for action in module.HIGH_RISK_ACTIONS:
            with self.subTest(action=action):
                result = self.plan(self.request(action=action),
                                   frozenset({action}))
                self.assertEqual(result["status"], "HUMAN_REQUIRED")
                self.assertIn("HIGH_RISK", result["human_reasons"])

    def test_canonical_human_reasons_only(self):
        result = self.plan(self.request(
            action="SUBMIT_FORM", confidence=.2, policy_green=False,
            security_incident=True, customer_human_request=True,
            legal_required=True, signature_required=True,
            money_amount=10, money_limit=0,
        ))
        self.assertTrue(set(result["human_reasons"]) <= module.CANONICAL_HUMAN_REASONS)
        self.assertFalse(result["dispatch_allowed"])

    def test_deny_unsafe_origins(self):
        for origin in ("http://example.com/", "https://example.com.evil/",
                       "https://user:pass@example.com/", "https://example.com/path",
                       "https://example.com/?q=1", "https://example.com:443/"):
            with self.subTest(origin=origin):
                result = self.plan(self.request(origin=origin,
                    approved_origins=(origin,)), frozenset({"READ_PAGE"}))
                self.assertIn("ORIGIN_APPROVAL_REQUIRED", result["blockers"])


if __name__ == "__main__":
    unittest.main()
