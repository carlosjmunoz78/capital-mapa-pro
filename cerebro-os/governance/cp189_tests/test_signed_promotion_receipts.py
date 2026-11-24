import unittest
from dataclasses import asdict, replace
from copy import deepcopy
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from governance.promotion_gate import REQUIRED_GATES
from governance.verified_promotion_gate import Candidate, decide_verified, digest
from governance.signed_promotion_receipts import canonical_receipt, signed_receipt_lookup

class SignedReceiptTests(unittest.TestCase):
    def setUp(self):
        self.c=Candidate("fenix","FACT-001","PREPROD","1.1.0","a"*40,"b"*64)
        self.keys={g:Ed25519PrivateKey.generate() for g in REQUIRED_GATES}
        self.trust={g:("independent-"+g,k.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)) for g,k in self.keys.items()}
        self.payloads={g:{"id":"receipt-"+g,"payload":g.encode()} for g in REQUIRED_GATES}
        self.records={g:{"body":{"schema":"cerebro.promotion.evidence.v1","gate":g,"candidate":asdict(self.c),"evidence_id":self.payloads[g]["id"],"payload_sha256":digest(g.encode()),"issuer":self.trust[g][0],"observed_at":90,"expires_at":110,"result":"PASS"}} for g in REQUIRED_GATES}
        for g in REQUIRED_GATES:self.sign(g)
    def sign(self,g,key=None):
        r=self.records[g];r["signature"]=(key or self.keys[g]).sign(canonical_receipt(r["body"])).hex()
    def decision(self, candidate=None, store=None, clock=lambda:100, **kw):
        lookup=signed_receipt_lookup(read_receipt=store or (lambda g,e:self.records.get(g)),trust=self.trust,clock=clock)
        opts=dict(candidate=candidate or self.c,gates={g:True for g in REQUIRED_GATES},evidence=self.payloads,trusted_lookup=lookup,issuer_by_gate={g:i for g,(i,_) in self.trust.items()},now=100,policy_decision="ALLOW",human_required=False)
        opts.update(kw)
        return decide_verified(**opts)
    def test_signed_full_set_review_only(self):
        r=self.decision();self.assertEqual(r["decision"],"PREPROD_REVIEW_CANDIDATE");self.assertFalse(r["deployment_authorized"])
    def test_unsigned(self):
        del self.records["backup"]["signature"];self.assertIn("backup",self.decision()["missing"])
    def test_tampered(self):
        self.records["cost"]["body"]["expires_at"]=120;self.assertIn("cost",self.decision()["missing"])
    def test_wrong_signer(self):
        self.sign("tribunal",self.keys["tests"]);self.assertIn("tribunal",self.decision()["missing"])
    def test_preprod_does_not_certify_prod(self):
        self.assertEqual(self.decision(replace(self.c,environment="PROD"))["decision"],"BLOCKED")
    def test_other_company(self):
        self.records["permissions"]["body"]["candidate"]["company_id"]="other";self.sign("permissions");self.assertIn("permissions",self.decision()["missing"])
    def test_other_artifact(self):
        self.records["tests"]["body"]["candidate"]["artifact_sha256"]="c"*64;self.sign("tests");self.assertIn("tests",self.decision()["missing"])
    def test_expired(self):
        self.records["cost"]["body"]["expires_at"]=100;self.sign("cost");self.assertIn("cost",self.decision()["missing"])
    def test_key_reuse(self):
        self.trust["tribunal"]=(self.trust["tribunal"][0],self.trust["tests"][1])
        with self.assertRaises(ValueError):self.decision()
    def test_false_result(self):
        self.records["cost"]["body"]["result"]="FAIL";self.sign("cost");self.assertIn("cost",self.decision()["missing"])
    def test_extra_field(self):
        self.records["tests"]["body"]["deployment_authorized"]=True;self.sign("tests");self.assertIn("tests",self.decision()["missing"])
    def test_store_unavailable(self):
        def fail(g,e): raise RuntimeError("offline")
        self.assertEqual(self.decision(store=fail)["decision"],"BLOCKED")
    def test_future_receipt(self):
        self.records["backup"]["body"]["observed_at"]=101;self.sign("backup");self.assertIn("backup",self.decision()["missing"])
    def test_policy_deny(self):
        self.assertEqual(self.decision(policy_decision="DENY")["decision"],"BLOCKED")
    def test_payload_change(self):
        self.payloads["backup"]["payload"]=b"changed";self.assertIn("backup",self.decision()["missing"])
