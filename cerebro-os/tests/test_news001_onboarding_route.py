import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"engines"/"CEREBRO-NEWS-001"))
from brevo_audience_gate import audience_eligibility
from news001_onboarding_route import route_verified_lead
START="2026-11-18T11:00:00+01:00"
BASE=dict(company_id="fenix",email="sample@example.org",suppressed=False,
    unsubscribed=False,hard_bounced=False,marketing_consent=True,
    consent_evidence_id="evid-verified-example",consent_at="2026-11-18T11:10:00+01:00",
    trusted_ingest_verified=True,lead_form_verified=True,
    double_opt_in_confirmed=True,lead_received_at="2026-11-18T11:04:00+01:00")
WEB_B2C=dict(BASE,persona="particular",origin="fenix_cerebro_leads",source_channel="web",consent_purpose="b2c_newsletter")
SOC_B2C=dict(BASE,persona="particular",origin="social_lead_form",source_channel="social",social_platform="Instagram",consent_purpose="b2c_newsletter")
WEB_B2B=dict(BASE,persona="inmobiliaria",origin="fenix_cerebro_leads",source_channel="web",consent_purpose="b2b_newsletter",salinas_screened=True,agency_name="Agencia Sierra")
SOC_B2B=dict(BASE,persona="inmobiliaria",origin="social_lead_form",source_channel="social",social_platform="LinkedIn",consent_purpose="b2b_newsletter",salinas_screened=True,agency_name="Agencia Sierra")
def run(c=WEB_B2C,ev="testnews001001"):return route_verified_lead(c,activation_at=START,event_id=ev)
class TestNews001Onboarding(unittest.TestCase):
 def test_new_web_particular(self):
  r=run();self.assertEqual(r["list_id"],17);self.assertFalse(r["send_enabled"])
 def test_social_particular(self):
  self.assertEqual(run(SOC_B2C)["template_family"],"b2c")
 def test_web_inmobiliaria(self):
  self.assertEqual(run(WEB_B2B)["list_id"],18)
 def test_social_inmobiliaria(self):
  self.assertEqual(run(SOC_B2B)["template_family"],"b2b")
 def test_salinas_web(self):
  self.assertEqual(run(dict(WEB_B2B,agency_name="Grupo Salinas"))["reason"],"USER_EXCLUDED_SALINAS")
 def test_salinas_social(self):
  self.assertEqual(run(dict(SOC_B2B,company_name="SÁLINAS"))["state"],"HOLD")
 def test_string_false_denied(self):
  self.assertEqual(run(dict(WEB_B2C,marketing_consent="false"))["state"],"HOLD")
 def test_privacy_not_newsletter(self):
  self.assertEqual(run(dict(WEB_B2C,marketing_consent=False,consent_privacy=True))["state"],"HOLD")
 def test_marketing_without_evidence(self):
  self.assertEqual(run(dict(WEB_B2C,consent_evidence_id=""))["state"],"HOLD")
 def test_single_click_consent_without_doi(self):
  self.assertEqual(run(dict(WEB_B2C,double_opt_in_confirmed=False))["state"],"PREPROD_DRY_RUN_ELIGIBLE")
 def test_unsubscribed(self):
  self.assertEqual(run(dict(WEB_B2B,unsubscribed=True))["state"],"HOLD")
 def test_hard_bounced(self):
  self.assertEqual(run(dict(SOC_B2C,hard_bounced=True))["state"],"HOLD")
 def test_old_particular(self):
  self.assertEqual(run(dict(WEB_B2C,lead_received_at="2026-11-17T09:00:00+01:00"))["state"],"HOLD")
 def test_old_brevo_particular(self):
  self.assertEqual(run(dict(WEB_B2C,origin="brevo_existing"))["state"],"HOLD")
 def test_wrong_company(self):
  self.assertEqual(run(dict(WEB_B2B,company_id="otra"))["state"],"HOLD")
 def test_missing_trusted_ingest(self):
  self.assertEqual(run(dict(WEB_B2C,trusted_ingest_verified=False))["state"],"HOLD")
 def test_missing_event_id(self):
  self.assertEqual(run(WEB_B2C,"")["state"],"HOLD")
 def test_missing_activation(self):
  self.assertEqual(route_verified_lead(WEB_B2C,activation_at=None,event_id="evt12345678")["state"],"HOLD")
 def test_social_missing_platform(self):
  self.assertEqual(run(dict(SOC_B2C,social_platform=""))["state"],"HOLD")
 def test_inmobiliaria_single_click_consent_without_doi(self):
  self.assertEqual(run(dict(WEB_B2B,double_opt_in_confirmed=False))["state"],"PREPROD_DRY_RUN_ELIGIBLE")
 def test_no_old_agency_send_without_consent(self):
  o=dict(BASE,persona="inmobiliaria",origin="brevo_existing",consent_purpose="b2b_newsletter",brevo_list_verified=True,salinas_screened=True,agency_name="Agencia")
  self.assertFalse(run(o)["send_enabled"])
 def test_success_is_not_authorization(self):
  for c in (WEB_B2C,SOC_B2C,WEB_B2B,SOC_B2B):
   x=run(c);self.assertEqual(x["state"],"PREPROD_DRY_RUN_ELIGIBLE")
   self.assertEqual(x["actions"],["plan_verified_subscribe","plan_single_optin_welcome","plan_following_weekly_issue"])
   self.assertFalse(x["eligible_for_live_send"]);self.assertFalse(x["brevo_contacts_mutation_enabled"])
 def test_no_send_or_write_methods(self):
  import news001_onboarding_route
  for n in ("send","send_mail","upsert_contact","write_to_brevo","send_campaign"):
   self.assertFalse(hasattr(news001_onboarding_route,n))
if __name__=="__main__":unittest.main()
