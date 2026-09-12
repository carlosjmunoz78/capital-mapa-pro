import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from facebook_text_direct_preflight import FacebookTextDirectPreflightRequest, audit_facebook_text_direct_preflight


def req(**changes):
    data = dict(
        company_id="fenix-capital", engine_id="SOC-PREFLIGHT", environment="TEST", version="1.0.0",
        publication_id="PUB1", run_id="RUN1", platform="Facebook", format="Texto orgánico simple",
        publication_state="Pendiente de publicar", real_publish_authorized=False,
        integration_authorized=True, integration_blocked=False, copy_reviewed=True,
        integration_state="Validación interna superada", technical_request="Solicitada",
        technical_state="Simulación preparada", production_order_id="OP1", production_state="READY",
        final_approved=True, qa_brand_state="OK", qa_legal_state="OK", production_format="texto",
        copy_blocks=1, calendar_item_id="CAL1", calendar_network="Facebook", calendar_channel="Organic",
        calendar_format="texto", calendar_review_state="OK", calendar_saturation_state="OK",
        calendar_legal_risk_state="LOW", calendar_state="READY", programming_id="PRG1",
        programming_state="READY", programming_control="OK", programming_type="publication",
    )
    data.update(changes)
    return FacebookTextDirectPreflightRequest(**data)


class FacebookTextDirectPreflightRuntimeTests(unittest.TestCase):
    def test_direct_record_contract_is_non_executing(self):
        result = audit_facebook_text_direct_preflight(req())
        self.assertEqual(result["status"], "DIRECT_CONTRACT_AUDITED")
        self.assertEqual(result["difference"], "ROLLUPS_IGNORED_DIRECT_RECORD_READ")
        self.assertEqual(result["platform_state"], "FACEBOOK_NOT_CALLED")
        self.assertFalse(result["external_action_allowed"])
        self.assertFalse(result["requires_human"])

    def test_publish_and_integration_gates_fail_closed(self):
        self.assertEqual(audit_facebook_text_direct_preflight(req(real_publish_authorized=True))["status"], "BLOCKED_REAL_PUBLISH_AUTH_PRESENT")
        self.assertEqual(audit_facebook_text_direct_preflight(req(integration_blocked=True))["status"], "BLOCKED_INTEGRATION")

    def test_content_contract_fail_closed(self):
        self.assertEqual(audit_facebook_text_direct_preflight(req(copy_blocks=0))["status"], "BLOCKED_CONTENT_NOT_APPROVED")
        self.assertEqual(audit_facebook_text_direct_preflight(req(copy_reviewed=False))["status"], "BLOCKED_CONTENT_NOT_APPROVED")

    def test_wrong_platform_and_environment_rejected(self):
        self.assertEqual(audit_facebook_text_direct_preflight(req(platform="Instagram"))["status"], "BLOCKED_WRONG_PLATFORM")
        with self.assertRaises(ValueError):
            audit_facebook_text_direct_preflight(req(environment="DEV"))


if __name__ == "__main__":
    unittest.main()
