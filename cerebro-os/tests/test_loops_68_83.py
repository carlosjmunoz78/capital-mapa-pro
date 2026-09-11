import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

c = load("commercial_engines_68_83", "commercial/engines.py")

class Loops68To83Tests(unittest.TestCase):
    def test_loop68_marketing_budget_and_roi(self):
        x = c.CampaignExperiment("fenix", "cmp", 100, 120, 10, 2, 300, "e")
        self.assertEqual("GREEN", x.decision); self.assertEqual(2.0, x.roi)
        self.assertEqual("HUMAN_REQUIRED", c.CampaignExperiment("fenix", "cmp", 121, 120, 10, 2, 300, "e").decision)

    def test_loop69_seo_prioritizes_and_gates_publish(self):
        backlog = c.seo_backlog((c.SeoFinding("a", 10, 2, "e1"), c.SeoFinding("b", 5, 5, "e2")))
        self.assertEqual(("a", "b"), backlog)
        self.assertEqual("BLOCKED", c.seo_publish_gate(qa_green=True, source_evidence=True, rollback_ref=""))
        self.assertEqual("GREEN", c.seo_publish_gate(qa_green=True, source_evidence=True, rollback_ref="rb"))

    def test_loop70_acquisition_respects_money_limit(self):
        status, channel = c.choose_acquisition_channel((c.AcquisitionChannel("seo", 0, 0, 5, 3), c.AcquisitionChannel("ads", 10, 20, 10, 4)))
        self.assertEqual("GREEN", status); self.assertEqual("seo", channel)
        self.assertEqual(("HUMAN_REQUIRED", "MONEY_LIMIT"), c.choose_acquisition_channel((c.AcquisitionChannel("ads", 21, 20, 1, 1),)))

    def test_loop71_lead_scoring_has_explanation_and_no_embedded_threshold(self):
        score = c.score_lead({"fit": .8, "urgency": .5}, {"fit": 2, "urgency": 1})
        self.assertEqual(2.1, score.score); self.assertEqual(2, len(score.explanation))

    def test_loop72_sales_next_action_is_deterministic(self):
        self.assertEqual("QUALIFY", c.sales_next_action("NEW")); self.assertEqual("LEARN", c.sales_next_action("LOST"))

    def test_loop73_communication_requires_consent_and_low_risk(self):
        self.assertEqual("GREEN", c.CommunicationRequest("fenix", "EMAIL", True, True, "e").decision())
        self.assertEqual("BLOCKED", c.CommunicationRequest("fenix", "EMAIL", False, True, "e").decision())
        self.assertEqual("HUMAN_REQUIRED", c.CommunicationRequest("fenix", "EMAIL", True, False, "e").decision())

    def test_loop74_notifications_dedupe_and_anti_saturation(self):
        rows = c.notification_digest((c.Notification("a", 1, "x"), c.Notification("a", 5, "y"), c.Notification("b", 2, "z")), limit=1)
        self.assertEqual(1, len(rows)); self.assertEqual(5, rows[0].priority)

    def test_loop75_voice_requires_consent_and_cost_guard(self):
        self.assertEqual(("HUMAN_REQUIRED", "LEGAL_REQUIRED"), c.VoiceSession("fenix", "s", False, "tr").decision())
        self.assertEqual(("HUMAN_REQUIRED", "MONEY_LIMIT"), c.VoiceSession("fenix", "s", True, "tr", 1, 0).decision())
        self.assertEqual(("GREEN", None), c.VoiceSession("fenix", "s", True, "tr", 0, 0).decision())

    def test_loop76_customer360_returns_refs_not_duplicate_records(self):
        view = c.customer_360("cust", (c.CustomerReference("CRM", "crm:1"), c.CustomerReference("APP", "app:2")))
        self.assertEqual("cust", view["customer_id"]); self.assertEqual(2, len(view["references"]))

    def test_loop77_cx_uses_normalized_signals(self):
        self.assertEqual(.5, c.cx_friction({"delay": .5}, {"delay": 2}))
        with self.assertRaises(ValueError): c.cx_friction({"delay": 2}, {"delay": 1})

    def test_loop78_retention_respects_threshold_and_money(self):
        self.assertEqual(("GREEN", "CALL"), c.RetentionDecision(.9, .8, "CALL").decision())
        self.assertEqual(("GREEN", "NO_ACTION"), c.RetentionDecision(.2, .8, "CALL").decision())
        self.assertEqual(("HUMAN_REQUIRED", "MONEY_LIMIT"), c.RetentionDecision(.9, .8, "OFFER", 5, 0).decision())

    def test_loop79_postsale_is_ordered(self):
        flow = c.PostSaleFlow(); self.assertEqual("CLOSE", flow.next_step())
        with self.assertRaises(ValueError): flow.complete("REVIEW")
        for step in c.POST_STEPS: flow.complete(step)
        self.assertIsNone(flow.next_step())

    def test_loop80_referral_eligibility_is_rule_based(self):
        self.assertEqual("GREEN", c.referral_eligibility(satisfaction=.9, successful_outcome=True, min_satisfaction=.8))
        self.assertEqual("NO_ACTION", c.referral_eligibility(satisfaction=.5, successful_outcome=True, min_satisfaction=.8))

    def test_loop81_reputation_escalates_negative_reviews(self):
        self.assertEqual(("HUMAN_REQUIRED", "HIGH_RISK"), c.Review(1, "bad", "e").triage())
        self.assertEqual(("GREEN", "LOW_RISK_RESPONSE_CANDIDATE"), c.Review(5, "great", "e").triage())

    def test_loop82_complaints_escalate_legal_and_high_risk(self):
        self.assertEqual(("HUMAN_REQUIRED", "LEGAL_REQUIRED"), c.Complaint("c1", "LOW", True, "e").decision())
        self.assertEqual(("HUMAN_REQUIRED", "HIGH_RISK"), c.Complaint("c2", "HIGH", False, "e").decision())
        self.assertEqual(("GREEN", None), c.Complaint("c3", "LOW", False, "e").decision())

    def test_loop83_competitor_intelligence_is_evidenced_and_diffable(self):
        old = c.CompetitorSnapshot("x", "2026-09-10T00:00:00+00:00", "src1", .9, (("price", "10"),))
        new = c.CompetitorSnapshot("x", "2026-09-11T00:00:00+00:00", "src2", .9, (("price", "12"),))
        self.assertEqual("GREEN", new.status()); self.assertEqual((("price", "10", "12"),), c.competitor_diff(old, new))
        low = c.CompetitorSnapshot("x", "2026-09-11T00:00:00+00:00", "src", .2, ())
        self.assertEqual("HUMAN_REQUIRED", low.status())

if __name__ == "__main__": unittest.main()
