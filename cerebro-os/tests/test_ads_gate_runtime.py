import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ads_gate import AdsOrder, evaluate_ads_preflight


class AdsGateRuntimeTests(unittest.TestCase):
    def order(self, **changes):
        data = dict(company_id="fenix-capital", engine_id="ADS-GATE", environment="LAB", version="1.0.0", ads_order_id="A1", run_id="R1", network="Meta", route_type="ADS", ad_account_id="ACC1", objective="LEADS", budget_amount=100.0, currency="EUR", budget_authorized=True, creative_ready=True, qa_passed=True, human_authorized=True)
        data.update(changes)
        return AdsOrder(**data)

    def test_complete_contract_routes_but_never_executes(self):
        result = evaluate_ads_preflight(self.order())
        self.assertEqual(result["status"], "ADS_PREFLIGHT_READY_ENGINE_DISABLED")
        self.assertEqual(result["route_receipt_status"], "ADS_ROUTED_NO_EXTERNAL_ACTION")
        self.assertFalse(result["external_action_allowed"])

    def test_duplicate_or_missing_gate_blocks(self):
        self.assertEqual(evaluate_ads_preflight(self.order(), duplicate_exists=True)["status"], "BLOCKED_PREFLIGHT")
        self.assertEqual(evaluate_ads_preflight(self.order(human_authorized=False))["status"], "BLOCKED_PREFLIGHT")

    def test_scope_in_idempotency_key(self):
        a = evaluate_ads_preflight(self.order(environment="LAB"))["idempotency_key"]
        b = evaluate_ads_preflight(self.order(environment="PROD"))["idempotency_key"]
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
