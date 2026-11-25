import unittest
from dataclasses import replace
from hashlib import sha256
from gateway.control_plane import control_decision
from gateway.control_plane_release import review_control
from governance.promotion_gate import REQUIRED_GATES
from governance.verified_promotion_gate import Candidate,TrustedEvidence

class ReleaseBoundary(unittest.TestCase):
    def setUp(self):
        self.c=Candidate("fenix","FACT-001","PROD","1.2.0","a"*40,"b"*64)
        self.refs={x:"fixture:"+x for x in ("route","policy","supervisor","tribunal","promotion")}
        self.base=dict(route_status="ROUTED",policy_decision="ALLOW",supervisor_state="GREEN",
            tribunal_approved=True,promotion_decision="PROD_CANDIDATE",evidence_refs=self.refs)
    def args(self,c=None):
        c=c or self.c
        evidence={g:{"id":"fixture:"+g,"payload":g.encode()} for g in REQUIRED_GATES}
        issuers={g:"fixture-issuer:"+g for g in REQUIRED_GATES}
        receipts={g:TrustedEvidence(g,c,evidence[g]["id"],sha256(g.encode()).hexdigest(),issuers[g],100,200,"PASS") for g in REQUIRED_GATES}
        return dict(candidate=c,**self.base,gates={g:True for g in REQUIRED_GATES},
            evidence=evidence,issuer_by_gate=issuers,now=150,trusted_lookup=lambda g,e:receipts[g])
    def test_old_new_string_evidence_is_not_authority(self):
        self.assertEqual(control_decision(**self.base,environment="PROD")["status"],"ALLOW_EXECUTION")
        a=self.args();a["trusted_lookup"]=lambda g,e:None
        r=review_control(**a)
        self.assertEqual(r["reason"],"VERIFIED_GATES_REQUIRED")
        self.assertEqual(len(r["review"]["missing"]),12)
    def test_even_twelve_verified_fixtures_are_only_candidate(self):
        r=review_control(**self.args())
        self.assertEqual(r["reason"],"SEPARATE_RELEASE_AUTHORITY_REQUIRED")
        self.assertEqual(r["review"]["decision"],"PROD_REVIEW_CANDIDATE")
        self.assertFalse(r["deployment_authorized"])
    def test_cross_environment(self):
        a=self.args();a["candidate"]=replace(self.c,environment="PREPROD");a["promotion_decision"]="PREPROD_GREEN"
        self.assertEqual(review_control(**a)["reason"],"VERIFIED_GATES_REQUIRED")
    def test_cross_company(self):
        a=self.args();a["candidate"]=replace(self.c,company_id="other")
        self.assertEqual(review_control(**a)["reason"],"VERIFIED_GATES_REQUIRED")
    def test_expired(self):
        a=self.args();a["now"]=200
        self.assertEqual(review_control(**a)["reason"],"VERIFIED_GATES_REQUIRED")
    def test_human_exception(self):
        a=self.args();a["human_required"]=True
        self.assertEqual(review_control(**a)["status"],"HUMAN_REQUIRED")
    def test_legacy_policy_and_supervision_remain_mandatory(self):
        for k,v in (("policy_decision","DENY"),("supervisor_state","RED"),("tribunal_approved",False),("promotion_decision","PREPROD_GREEN")):
            a=self.args();a[k]=v
            self.assertEqual(review_control(**a)["status"],"BLOCKED")
            self.assertFalse(review_control(**a)["deployment_authorized"])
    def test_preprod_review_only(self):
        a=self.args(replace(self.c,environment="PREPROD"));a["promotion_decision"]="PREPROD_GREEN"
        self.assertEqual(review_control(**a)["review"]["decision"],"PREPROD_REVIEW_CANDIDATE")
        self.assertFalse(review_control(**a)["deployment_authorized"])
