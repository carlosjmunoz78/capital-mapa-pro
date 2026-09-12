import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from facebook_v4_input_contracts import FacebookV4InputEvidence, validate_v4_input_contract


BASE = dict(
    company_id="fenix",
    engine_id="facebook-v4",
    environment="PROD",
    version="v1",
    publication_id="pub-1",
    run_id="run-1",
    technical_format_ok=True,
    production_final=True,
    final_approved=True,
    production_gate_ok=True,
    incoherence_absent=True,
    brand_qa_approved=True,
    legal_qa_ok=True,
    copy_present=True,
    channel_facebook_social=True,
    supervisor_ready=True,
    schedule_programmed=True,
    schedule_due=True,
    schedule_incident_absent=True,
    run_ids_match=True,
    integration_unblocked=True,
    copy_reviewed=True,
    authorization_once=True,
    override_record_matches=True,
    override_not_expired=True,
    idempotency_clear=True,
)


def req(fmt, **kwargs):
    data = dict(BASE)
    data["format"] = fmt
    data.update(kwargs)
    return FacebookV4InputEvidence(**data)


class FacebookV4InputContractsTest(unittest.TestCase):
    def test_text_requires_t48(self):
        out = validate_v4_input_contract(req("text"))
        self.assertEqual(out["status"], "BLOCKED_INPUT_CONTRACT")
        self.assertIn("t48_approved", out["failed_gates"])
        self.assertFalse(out["external_action_allowed"])

    def test_text_green_contract_still_requires_signature(self):
        out = validate_v4_input_contract(req("text", t48_approved=True, t48_date_valid=True, t48_version_locked=True, t48_hash_present=True))
        self.assertEqual(out["status"], "INPUT_CONTRACT_GREEN")
        self.assertEqual(out["human_reason"], "SIGNATURE_REQUIRED")
        self.assertFalse(out["facebook_mutation_allowed"])

    def test_link_specific_gates(self):
        out = validate_v4_input_contract(req("link", t48_approved=True, t48_date_valid=True, t48_version_locked=True, t48_hash_present=True))
        self.assertIn("final_url_present", out["failed_gates"])
        self.assertIn("utm_required", out["failed_gates"])
        self.assertIn("domain_allowed", out["failed_gates"])

    def test_image_asset_and_t48(self):
        out = validate_v4_input_contract(req("image", t48_approved=True, t48_date_valid=True, t48_version_locked=True, t48_hash_present=True, asset_approved=True, asset_principal=True, asset_type="Imagen", asset_brand_qa_approved=True, asset_legal_qa_ok=True))
        self.assertEqual(out["status"], "INPUT_CONTRACT_GREEN")

    def test_reel_exact_asset_constraints(self):
        out = validate_v4_input_contract(req("reel", asset_approved=True, asset_principal=True, asset_type="Vídeo", asset_brand_qa_approved=True, asset_legal_qa_ok=True, orientation="Vertical", width=540, height=960, duration_seconds=90, mime="video/mp4"))
        self.assertEqual(out["status"], "INPUT_CONTRACT_GREEN")
        bad = validate_v4_input_contract(req("reel", asset_approved=True, asset_principal=True, asset_type="Vídeo", asset_brand_qa_approved=True, asset_legal_qa_ok=True, orientation="Horizontal", width=539, height=959, duration_seconds=91, mime="video/quicktime"))
        self.assertEqual(bad["status"], "BLOCKED_INPUT_CONTRACT")
        for gate in ("orientation_vertical", "width_min_540", "height_min_960", "duration_3_90", "mime_video_mp4"):
            self.assertIn(gate, bad["failed_gates"])

    def test_carousel_requires_2_to_30_and_explicit_authorization(self):
        out = validate_v4_input_contract(req("carousel", photo_count=2, explicit_authorized=True))
        self.assertEqual(out["status"], "INPUT_CONTRACT_GREEN")
        bad = validate_v4_input_contract(req("carousel", photo_count=31, explicit_authorized=False))
        self.assertIn("photo_count_2_30", bad["failed_gates"])
        self.assertEqual(bad["human_reason"], "SIGNATURE_REQUIRED")

    def test_video_long_requires_explicit_authorization(self):
        out = validate_v4_input_contract(req("video_long", explicit_authorized=False))
        self.assertEqual(out["status"], "BLOCKED_INPUT_CONTRACT")
        self.assertEqual(out["human_reason"], "SIGNATURE_REQUIRED")

    def test_non_prod_fail_closed(self):
        data = dict(BASE)
        data.update(format="text", environment="TEST")
        out = validate_v4_input_contract(FacebookV4InputEvidence(**data))
        self.assertEqual(out["status"], "ENVIRONMENT_NOT_PROD")
        self.assertEqual(out["human_reason"], "POLICY_CONFLICT")


if __name__ == "__main__":
    unittest.main()
