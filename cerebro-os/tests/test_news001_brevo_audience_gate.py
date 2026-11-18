import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engines" / "CEREBRO-NEWS-001"))
from brevo_audience_gate import audience_eligibility

LAUNCH = "2026-11-18T10:00:00+01:00"
BASE = dict(company_id="fenix",email="example@example.org",suppressed=False,
            unsubscribed=False,hard_bounced=False,marketing_consent=True,
            consent_evidence_id="test-evidence-001",consent_at="2026-11-17T15:00:00+01:00")
B2B = dict(BASE,persona="inmobiliaria",origin="brevo_existing",
           consent_purpose="b2b_newsletter",brevo_list_verified=True,salinas_screened=True,agency_name="Agencia Ejemplo")
B2C = dict(BASE,persona="particular",origin="fenix_cerebro_leads",
           consent_purpose="b2c_newsletter",lead_received_at="2026-11-18T10:05:00+01:00",
           double_opt_in_confirmed=True)

class TestNews001Cohorts(unittest.TestCase):
    def check(self,x,expected):
        self.assertEqual(audience_eligibility(x,activation_at=LAUNCH)["state"],expected)
    def test_existing_agency_eligible_for_test_only(self):
        r=audience_eligibility(B2B,activation_at=LAUNCH)
        self.assertEqual(r["segment"],"INMOBILIARIAS_COLABORADORAS")
        self.assertFalse(r["send_authorized"])
    def test_new_particular_eligible_for_test_only(self):
        r=audience_eligibility(B2C,activation_at=LAUNCH)
        self.assertEqual(r["segment"],"PARTICULARES_NUEVOS")
        self.assertFalse(r["contact_mutation_authorized"])
    def test_old_particular_excluded(self):
        self.check(dict(B2C,lead_received_at="2026-11-16T10:00:00+01:00"),"HOLD")
    def test_old_brevo_particular_excluded(self):
        self.check(dict(B2C,origin="brevo_existing"),"HOLD")
    def test_new_agency_not_automatically_imported(self):
        self.check(dict(B2B,origin="fenix_cerebro_leads"),"HOLD")
    def test_marketing_false_denied(self):
        self.check(dict(B2C,marketing_consent=False),"HOLD")
    def test_string_false_denied(self):
        self.check(dict(B2C,marketing_consent="false"),"HOLD")
    def test_string_true_denied(self):
        self.check(dict(B2C,marketing_consent="true"),"HOLD")
    def test_evidence_missing_denied(self):
        self.check(dict(B2B,consent_evidence_id=""),"HOLD")
    def test_no_consent_timestamp_denied(self):
        self.check(dict(B2B,consent_at=""),"HOLD")
    def test_suppressed_denied(self):
        self.check(dict(B2C,suppressed=True),"HOLD")
    def test_unsubscribed_denied(self):
        self.check(dict(B2B,unsubscribed=True),"HOLD")
    def test_unknown_unsubscribed_denied(self):
        self.check({k:v for k,v in B2B.items() if k!="unsubscribed"},"HOLD")
    def test_hard_bounced_denied(self):
        self.check(dict(B2C,hard_bounced=True),"HOLD")
    def test_wrong_consent_purpose_denied(self):
        self.check(dict(B2B,consent_purpose="b2c_newsletter"),"HOLD")
    def test_missing_list_proof_denied(self):
        self.check(dict(B2B,brevo_list_verified=False),"HOLD")
    def test_missing_double_opt_in_denied(self):
        self.check(dict(B2C,double_opt_in_confirmed=False),"HOLD")
    def test_invalid_activation_denied(self):
        self.assertEqual(audience_eligibility(B2C,activation_at="not-a-date")["state"],"HOLD")
    def test_unknown_company_denied(self):
        self.check(dict(B2B,company_id="other"),"HOLD")
    def test_salinas_direct_exclusion(self):
        r=audience_eligibility(dict(B2B,agency_name="Inmobiliaria Salinas"),activation_at=LAUNCH)
        self.assertEqual(r["reason"],"USER_EXCLUDED_SALINAS")
    def test_salinas_unicode_accent(self):
        r=audience_eligibility(dict(B2B,agency_name="SÁLINAS Inmobiliaria"),activation_at=LAUNCH)
        self.assertEqual(r["reason"],"USER_EXCLUDED_SALINAS")
    def test_salinas_company_name(self):
        self.check(dict(B2B,company_name="Grupo Salinas"),"HOLD")
    def test_salinas_contact_name(self):
        self.check(dict(B2B,contact_name="María Salinas"),"HOLD")
    def test_salinas_screening_not_verified(self):
        self.check(dict(B2B,salinas_screened=False),"HOLD")
    def test_other_agency_in_brevo_valid(self):
        r=audience_eligibility(dict(B2B,agency_name="Otra agencia"),activation_at=LAUNCH)
        self.assertEqual(r["segment"],"INMOBILIARIAS_COLABORADORAS")
        self.assertFalse(r["send_authorized"])
    def test_social_instagram_new_lead(self):
        c=dict(B2C,origin="social_lead_form",source_channel="social",social_platform="Instagram",lead_form_verified=True)
        self.assertEqual(audience_eligibility(c,activation_at=LAUNCH)["segment"],"PARTICULARES_NUEVOS")
    def test_social_other_network_new_lead(self):
        c=dict(B2C,origin="social_lead_form",source_channel="social",social_platform="red-social-nueva",lead_form_verified=True)
        self.assertEqual(audience_eligibility(c,activation_at=LAUNCH)["segment"],"PARTICULARES_NUEVOS")
    def test_social_facebook_new_lead(self):
        c=dict(B2C,origin="social_lead_form",source_channel="social",social_platform="Facebook",lead_form_verified=True)
        self.assertEqual(audience_eligibility(c,activation_at=LAUNCH)["segment"],"PARTICULARES_NUEVOS")
    def test_social_no_verified_form_denied(self):
        self.check(dict(B2C,origin="social_lead_form",source_channel="social",social_platform="Instagram",lead_form_verified=False),"HOLD")
    def test_social_missing_platform_denied(self):
        self.check(dict(B2C,origin="social_lead_form",source_channel="social",lead_form_verified=True),"HOLD")
    def test_social_old_lead_denied(self):
        self.check(dict(B2C,origin="social_lead_form",source_channel="social",social_platform="Facebook",lead_form_verified=True,lead_received_at="2026-11-01T09:00:00+01:00"),"HOLD")
    def test_web_new_lead(self):
        self.assertEqual(audience_eligibility(dict(B2C,source_channel="web"),activation_at=LAUNCH)["segment"],"PARTICULARES_NUEVOS")
    def test_old_brevo_particular_denied(self):
        self.check(dict(B2C,origin="brevo_existing"),"HOLD")
    def test_invalid_source_channel(self):
        self.check(dict(B2C,source_channel="unknown"),"HOLD")
    def test_no_io_or_exported_send(self):
        import brevo_audience_gate
        self.assertFalse(hasattr(brevo_audience_gate,"send_campaign"))
if __name__=="__main__":unittest.main()
