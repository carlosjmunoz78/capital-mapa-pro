import os
import sys
import unittest

HERE = os.path.dirname(__file__)
RUNTIME = os.path.abspath(os.path.join(HERE, "..", "runtime"))
if RUNTIME not in sys.path:
    sys.path.insert(0, RUNTIME)

from factory_image_native_contract import ImageAssetRequest, assess_image_asset_request


class FactoryImageNativeContractTests(unittest.TestCase):
    def req(self, **overrides):
        data = dict(
            company_id="fenix",
            engine_id="FACTORY-IMAGE",
            environment="LAB",
            version="1.0.0",
            run_id="RUN-001",
            production_order_id="ORDER-001",
            format="instagram-post",
            prompt="Casa luminosa en Córdoba",
            existing_asset_count=0,
            paid_provider_enabled=False,
            provider_cost_eur=0.0,
            money_limit_eur=0.0,
        )
        data.update(overrides)
        return ImageAssetRequest(**data)

    def test_duplicate_assets_fail_closed_high_risk(self):
        out = assess_image_asset_request(self.req(existing_asset_count=2))
        self.assertEqual(out["status"], "BLOCKED_DUPLICATES")
        self.assertEqual(out["human_reason"], "HIGH_RISK")
        self.assertFalse(out["external_action_allowed"])
        self.assertTrue(out["old_preserved"])

    def test_one_asset_is_reused_without_generation(self):
        out = assess_image_asset_request(self.req(existing_asset_count=1))
        self.assertEqual(out["status"], "REUSE_EXISTING_ASSET")
        self.assertTrue(out["reuse_existing"])
        self.assertFalse(out["generate_allowed"])

    def test_zero_cost_default_never_requires_paid_ai(self):
        out = assess_image_asset_request(self.req())
        self.assertEqual(out["status"], "QUEUED_ZERO_COST_PROVIDER_NOT_CONNECTED")
        self.assertFalse(out["additional_paid_ai_required"])
        self.assertFalse(out["external_action_allowed"])

    def test_money_limit_blocks_paid_provider(self):
        out = assess_image_asset_request(self.req(paid_provider_enabled=True, provider_cost_eur=2.0, money_limit_eur=1.0))
        self.assertEqual(out["status"], "BLOCKED_MONEY_LIMIT")
        self.assertEqual(out["human_reason"], "MONEY_LIMIT")
        self.assertFalse(out["generate_allowed"])

    def test_prod_provider_ready_still_requires_signature_and_no_execution(self):
        out = assess_image_asset_request(self.req(environment="PROD", paid_provider_enabled=True, provider_cost_eur=0.5, money_limit_eur=1.0))
        self.assertEqual(out["status"], "PROVIDER_READY_BUT_EXECUTION_GATED")
        self.assertEqual(out["human_reason"], "SIGNATURE_REQUIRED")
        self.assertFalse(out["external_action_allowed"])
        self.assertTrue(out["legacy_scenario_must_remain_inactive"])


if __name__ == "__main__":
    unittest.main()
