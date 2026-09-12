import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from facebook_image_preflight import FacebookImagePreflightRequest, plan_facebook_image_preflight


def req(**changes):
    data = dict(
        company_id="fenix-capital", engine_id="SOC-PREFLIGHT", environment="TEST", version="1.0.0",
        publication_id="PUB1", run_id="RUN1", format="imagen", real_publish_authorized=False,
        integration_authorized=True, integration_blocked=False, copy_reviewed=True,
        production_order_id="OP1", production_state="READY", final_approved=True,
        qa_brand_state="OK", qa_legal_state="OK", calendar_item_id="CAL1",
        calendar_network="Facebook", calendar_channel="Organic", calendar_format="imagen",
        calendar_review_state="OK", calendar_saturation_state="OK", calendar_legal_risk_state="LOW",
        asset_id="ASSET1", asset_state="READY", asset_type="image", asset_main=True,
        asset_url="https://example.com/image.jpg", asset_size=123456, asset_width=1080, asset_height=1350,
        asset_mime="image/jpeg", asset_qa_brand="OK", asset_qa_legal="OK", asset_rights="OWNED",
        http_status=200, programming_id="PRG1", programming_order_id="OP1", programming_run_id="RUN1",
        programming_state="READY", programming_type="publication", programming_control="OK",
        programming_incident=False, programming_date="2026-09-12T12:00:00Z",
        programming_draft_url="https://example.com/draft",
    )
    data.update(changes)
    return FacebookImagePreflightRequest(**data)


class FacebookImagePreflightRuntimeTests(unittest.TestCase):
    def test_valid_contract_is_non_executing(self):
        result = plan_facebook_image_preflight(req())
        self.assertEqual(result["status"], "DIRECT_CONTRACT_VALIDATED")
        self.assertEqual(result["platform_state"], "FACEBOOK_NOT_CALLED")
        self.assertFalse(result["external_action_allowed"])
        self.assertFalse(result["requires_human"])

    def test_integration_and_real_publish_fail_closed(self):
        self.assertEqual(plan_facebook_image_preflight(req(integration_blocked=True))["status"], "BLOCKED_INTEGRATION")
        self.assertEqual(plan_facebook_image_preflight(req(real_publish_authorized=True))["status"], "BLOCKED_REAL_PUBLISH_AUTH_PRESENT")

    def test_asset_contract_failures_block(self):
        self.assertEqual(plan_facebook_image_preflight(req(asset_main=False))["status"], "BLOCKED_ASSET_NOT_MAIN")
        self.assertEqual(plan_facebook_image_preflight(req(asset_mime="image/gif"))["status"], "BLOCKED_UNSUPPORTED_IMAGE_FORMAT")
        self.assertEqual(plan_facebook_image_preflight(req(http_status=404))["status"], "BLOCKED_ASSET_UNREACHABLE")
        self.assertEqual(plan_facebook_image_preflight(req(asset_width=0))["status"], "BLOCKED_INVALID_ASSET_METADATA")

    def test_relations_are_consistent(self):
        self.assertEqual(plan_facebook_image_preflight(req(programming_order_id="OP2"))["status"], "BLOCKED_ORDER_RELATION_MISMATCH")
        self.assertEqual(plan_facebook_image_preflight(req(programming_run_id="RUN2"))["status"], "BLOCKED_RUN_ID_MISMATCH")

    def test_invalid_environment_rejected(self):
        with self.assertRaises(ValueError):
            plan_facebook_image_preflight(req(environment="DEV"))


if __name__ == "__main__":
    unittest.main()
