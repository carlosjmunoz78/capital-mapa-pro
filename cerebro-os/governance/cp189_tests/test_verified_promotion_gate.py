import unittest
from dataclasses import replace
from governance.verified_promotion_gate import Candidate, TrustedEvidence, decide_verified, digest
from governance.promotion_gate import REQUIRED_GATES, decide_promotion

class VerifiedPromotionTests(unittest.TestCase):
    def setUp(self):
        self.c=Candidate("fenix","FACT-001","PREPROD","1.0.0","a"*40,"b"*64)
        self.g={g:True for g in REQUIRED_GATES}
        self.i={g:"authority-"+g for g in REQUIRED_GATES}
        self.e={g:{"id":"receipt-"+g,"payload":g.encode()} for g in REQUIRED_GATES}
        self.r={g:TrustedEvidence(g,self.c,self.e[g]["id"],digest(self.e[g]["payload"]),self.i[g],90,110,"PASS") for g in REQUIRED_GATES}
    def run_gate(self, **kw):
        args=dict(candidate=self.c,gates=self.g,evidence=self.e,trusted_lookup=lambda g,e:self.r.get(g),issuer_by_gate=self.i,now=100,policy_decision="ALLOW",human_required=False)
        args.update(kw)
        return decide_verified(**args)
    def test_valid_only_review_candidate(self):
        r=self.run_gate();self.assertEqual(r["decision"],"PREPROD_REVIEW_CANDIDATE");self.assertFalse(r["deployment_authorized"])
    def test_legacy_reference_only_does_not_suffice(self):
        self.assertEqual(decide_promotion(engine_id="FACT-001",environment="PREPROD",gates=self.g,evidence_refs={g:"fake" for g in self.g})["decision"],"PREPROD_GREEN")
        self.assertEqual(self.run_gate(trusted_lookup=lambda g,e:None)["decision"],"BLOCKED")
    def test_string_bool(self):
        self.g["cost"]="true";self.assertIn("cost",self.run_gate()["missing"])
    def test_payload_tampering(self):
        self.e["backup"]["payload"]=b"tampered";self.assertIn("backup",self.run_gate()["missing"])
    def test_wrong_candidate(self):
        self.r["permissions"]=replace(self.r["permissions"],candidate=replace(self.c,company_id="foreign"));self.assertIn("permissions",self.run_gate()["missing"])
    def test_wrong_artifact(self):
        self.r["tests"]=replace(self.r["tests"],candidate=replace(self.c,artifact_sha256="c"*64));self.assertIn("tests",self.run_gate()["missing"])
    def test_stale(self):
        self.r["cost"]=replace(self.r["cost"],expires_at=100);self.assertIn("cost",self.run_gate()["missing"])
    def test_untrusted_issuer(self):
        self.r["tribunal"]=replace(self.r["tribunal"],issuer="caller");self.assertIn("tribunal",self.run_gate()["missing"])
    def test_duplicate_receipt(self):
        self.e["rebuild"]["id"]=self.e["backup"]["id"];self.assertIn("rebuild",self.run_gate()["missing"])
    def test_provider_failure(self):
        def down(g,e): raise RuntimeError("unavailable")
        self.assertEqual(self.run_gate(trusted_lookup=down)["decision"],"BLOCKED")
    def test_missing_gate(self):
        del self.e["policy"];self.assertEqual(self.run_gate()["reason"],"GATE_SET_MISMATCH")
    def test_policy_and_human(self):
        self.assertEqual(self.run_gate(policy_decision="DENY")["decision"],"BLOCKED")
        self.assertEqual(self.run_gate(human_required=True)["decision"],"HUMAN_REQUIRED")
    def test_prod_not_auto_authorized(self):
        c=replace(self.c,environment="PROD")
        self.r={g:replace(r,candidate=c) for g,r in self.r.items()}
        r=self.run_gate(candidate=c);self.assertEqual(r["decision"],"PROD_REVIEW_CANDIDATE");self.assertFalse(r["deployment_authorized"])

if __name__=="__main__": unittest.main()
