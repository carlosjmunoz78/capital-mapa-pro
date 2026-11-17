import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"engines"/"CEREBRO-NEWS-001"))
from brevo_free_daily_planner import simulate_day,MAX_FREE_DAY
def job(kind="newsletter_b2b",newsletter="edition-01",contact="agency-01",**extra):
    base={"company_id":"fenix","kind":kind,"audience":"b2c" if kind.endswith("b2c") else "b2b",
          "cohort_gate":"ELIGIBLE_FOR_PREPROD_TEST_ONLY","unsubscribed":False,
          "suppressed":False,"contact_evidence_verified":True,
          "editorial_approved":True,"visual_qa_pass":True,
          "newsletter_id":newsletter,"contact_ref":contact}
    return {**base,**extra}
def plan(jobs,**extra):
    return simulate_day(jobs,account_quota_verified=True,provider_daily_limit=300,
                        provider_remaining=300,**extra)
class Planner(unittest.TestCase):
    def test_default_blocks_without_quota(self):
        self.assertEqual(simulate_day([job()])["state"],"BLOCKED_ACCOUNT_QUOTA_UNVERIFIED")
    def test_verified_quota_never_sends(self):
        r=plan([job()]);self.assertEqual(len(r["planned"]),1);self.assertFalse(r["planned"][0]["send_authorized"]);self.assertEqual(r["sent_count"],0)
    def test_max_free_cap(self):
        r=plan([job(contact=str(i)) for i in range(400)]);self.assertEqual(len(r["planned"]),MAX_FREE_DAY);self.assertEqual(r["deferred_count"],100)
    def test_remaining_lower_than_limit(self):
        r=simulate_day([job(contact=str(i)) for i in range(200)],account_quota_verified=True,provider_daily_limit=300,provider_remaining=30);self.assertEqual(len(r["planned"]),30)
    def test_zero_remaining(self):
        r=simulate_day([job()],account_quota_verified=True,provider_daily_limit=300,provider_remaining=0);self.assertEqual(r["planned"],[])
    def test_provider_below_300(self):
        r=simulate_day([job(contact=str(i)) for i in range(90)],account_quota_verified=True,provider_daily_limit=40,provider_remaining=40);self.assertEqual(len(r["planned"]),40)
    def test_invalid_negative_quota(self):
        r=simulate_day([],account_quota_verified=True,provider_daily_limit=300,provider_remaining=-1);self.assertEqual(r["state"],"BLOCKED_INVALID_QUOTA")
    def test_invalid_above_quota(self):
        r=simulate_day([],account_quota_verified=True,provider_daily_limit=300,provider_remaining=301);self.assertEqual(r["state"],"BLOCKED_INVALID_QUOTA")
    def test_dedupe_same_event(self):
        r=plan([job(),job()]);self.assertEqual(len(r["planned"]),1);self.assertEqual(r["deduplicated_count"],1)
    def test_dedupe_previously_sent(self):
        a=plan([job()])["planned"][0]["idempotency_key"]
        r=plan([job()],previously_dispatched=[a]);self.assertEqual(len(r["planned"]),0)
    def test_prioritize_welcome(self):
        r=simulate_day([job(contact="newsletter"),job(kind="welcome_b2c",contact="new")],account_quota_verified=True,provider_daily_limit=300,provider_remaining=1);self.assertEqual(r["planned"][0]["kind"],"welcome_b2c")
    def test_unsubscribed_is_held(self):
        r=plan([job(unsubscribed=True)]);self.assertEqual(r["held_count"],1)
    def test_unknown_suppression_is_held(self):
        r=plan([job(suppressed=None)]);self.assertEqual(r["held_count"],1)
    def test_no_consent_proof_is_held(self):
        r=plan([job(contact_evidence_verified=False)]);self.assertEqual(r["held_count"],1)
    def test_qa_images_fail_is_held(self):
        r=plan([job(visual_qa_pass=False)]);self.assertEqual(r["held_count"],1)
    def test_qa_editorial_fail_is_held(self):
        r=plan([job(editorial_approved=False)]);self.assertEqual(r["held_count"],1)
    def test_wrong_cohort_is_held(self):
        r=plan([job(cohort_gate="HOLD")]);self.assertEqual(r["held_count"],1)
    def test_company_scope_is_held(self):
        r=plan([job(company_id="other")]);self.assertEqual(r["held_count"],1)
    def test_wrong_kind_segment_is_held(self):
        r=plan([job(audience="b2c")]);self.assertEqual(r["held_count"],1)
    def test_round_robin_campaigns(self):
        jobs=[job("newsletter_b2b",contact="agency"+str(i)) for i in range(4)]
        jobs += [job("newsletter_b2c",contact="user"+str(i)) for i in range(4)]
        r=simulate_day(jobs,account_quota_verified=True,provider_daily_limit=300,provider_remaining=4)
        self.assertEqual([x["audience"] for x in r["planned"]],["b2b","b2c","b2b","b2c"])
    def test_no_network_logic(self):
        import brevo_free_daily_planner
        self.assertFalse(hasattr(brevo_free_daily_planner,"send"))
if __name__=="__main__": unittest.main()
