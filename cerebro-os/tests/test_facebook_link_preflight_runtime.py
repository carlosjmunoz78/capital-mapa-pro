import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from facebook_link_preflight import FacebookLinkPreflightRequest, plan_facebook_link_preflight


def req(**changes):
    data = dict(
        company_id="fenix-capital",
        engine_id="SOC-PREFLIGHT",
        environment="TEST",
        version="1.0.0",
        publication_id="PUB1",
        run_id="RUN1",
        format="enlace",
        real_publish_authorized=False,
        integration_authorized=True,
        copy_reviewed=True,
        utm_required=True,
        domain_allowed=True,
        production_order_id="OP1",
        production_state="READY",
        final_approved=True,
        qa_brand_state="OK",
        qa_legal_state="OK",
        final_url="https://example.com/landing",
        calendar_item_id="CAL1",
        calendar_network="Facebook",
        calendar_channel="Organic",
        calendar_format="enlace",
        calendar_review_state="OK",
        calendar_saturation_state="OK",
        calendar_legal_risk_state="LOW",
        programming_id="PRG1",
        programming_order_id="OP1",
        programming_run_id="RUN1",
        programming_state="READY",
        programming_type="publication",
        programming_control="OK",
        programming_incident=False,
        programming_date="2026-09-12T12:00:00Z",
        programming_draft_url="https://example.com/draft",
    )
    data.update(changes)
    return FacebookLinkPreflightRequest(**data)


class FacebookLinkPreflightRuntimeTests(unittest.TestCase):
    def test_valid_old_contract_is_non_executing(self):
        result = plan_facebook_link_preflight(req())
        self.assertEqual(result["status"], "DIRECT_CONTRACT_VALIDATED")
        self.assertEqual(result["platform_state"], "FACEBOOK_NOT_CALLED")
        self.assertFalse(result["external_action_allowed"])
        self.assertFalse(result["requires_human"])

    def test_real_publish_auth_fails_closed(self):
        result = plan_facebook_link_preflight(req(real_publish_authorized=True))
        self.assertEqual(result["status"], "BLOCKED_REAL_PUBLISH_AUTH_PRESENT")
        self.assertTrue(result["requires_human"])

    def test_domain_and_url_are_required_for_link(self):
        self.assertEqual(plan_facebook_link_preflight(req(domain_allowed=False))["status"], "BLOCKED_DOMAIN_NOT_ALLOWED")
        self.assertEqual(plan_facebook_link_preflight(req(final_url=""))["status"], "BLOCKED_MISSING_FINAL_URL")

    def test_relation_and_run_mismatch_fail_closed(self):
        self.assertEqual(plan_facebook_link_preflight(req(programming_order_id="OP2"))["status"], "BLOCKED_ORDER_RELATION_MISMATCH")
        self.assertEqual(plan_facebook_link_preflight(req(programming_run_id="RUN2"))["status"], "BLOCKED_RUN_ID_MISMATCH")

    def test_invalid_environment_rejected(self):
        with self.assertRaises(ValueError):
            plan_facebook_link_preflight(req(environment="DEV"))


if __name__ == "__main__":
    unittest.main()
