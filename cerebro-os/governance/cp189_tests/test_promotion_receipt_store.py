import json
import sqlite3
import tempfile
import unittest
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from governance.promotion_gate import REQUIRED_GATES
from governance.verified_promotion_gate import Candidate
from governance.signed_promotion_receipts import canonical_receipt
from governance.promotion_receipt_store import review_stored_candidate

class ReceiptStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"receipts.sqlite"
        self.candidate=Candidate("fenix","FACT-001","PREPROD","1.1.0","a"*40,"b"*64)
        self.trust={}
        self.ids={}
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE promotion_receipts(gate TEXT,evidence_id TEXT,payload BLOB,envelope TEXT,PRIMARY KEY(gate,evidence_id))")
            for g in REQUIRED_GATES:
                k=Ed25519PrivateKey.generate()
                issuer="test:"+g
                self.trust[g]=(issuer,k.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw))
                eid="test-receipt:"+g
                self.ids[g]=eid
                payload=("synthetic:"+g).encode()
                b=dict(schema="cerebro.promotion.evidence.v1",gate=g,candidate=asdict(self.candidate),evidence_id=eid,payload_sha256=sha256(payload).hexdigest(),issuer=issuer,observed_at=100,expires_at=200,result="PASS")
                db.execute("INSERT INTO promotion_receipts VALUES(?,?,?,?)",(g,eid,payload,json.dumps({"body":b,"signature":k.sign(canonical_receipt(b)).hex()})))
    def review(self,**kw):
        args=dict(candidate=self.candidate,receipt_ids=self.ids,store_path=self.path,trust=self.trust,clock=lambda:150,policy_decision="ALLOW",human_required=False)
        args.update(kw)
        return review_stored_candidate(**args)
    def test_complete_readonly_snapshot(self):
        before=self.path.read_bytes()
        r=self.review()
        self.assertEqual(r["decision"],"PREPROD_REVIEW_CANDIDATE")
        self.assertIs(r["deployment_authorized"],False)
        self.assertEqual(self.path.read_bytes(),before)
        self.assertEqual(self.review()["decision"],r["decision"])
    def test_missing_file_does_not_create(self):
        p=self.path.parent/"missing.sqlite"
        self.assertEqual(self.review(store_path=p)["decision"],"BLOCKED")
        self.assertFalse(p.exists())
    def test_missing_receipt(self):
        with sqlite3.connect(self.path) as db:
            db.execute("DELETE FROM promotion_receipts WHERE gate='backup'")
        self.assertIn("backup",self.review()["missing"])
    def test_tampered_payload(self):
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE promotion_receipts SET payload=? WHERE gate='tests'",(b"modified",))
        self.assertIn("tests",self.review()["missing"])
    def test_expired(self):
        self.assertEqual(self.review(clock=lambda:200)["decision"],"BLOCKED")
    def test_cross_environment(self):
        self.assertEqual(self.review(candidate=replace(self.candidate,environment="PROD"))["decision"],"BLOCKED")
    def test_policy_and_human(self):
        self.assertEqual(self.review(policy_decision="DENY")["decision"],"BLOCKED")
        self.assertEqual(self.review(human_required=True)["decision"],"HUMAN_REQUIRED")
    def test_duplicate_json_key(self):
        with sqlite3.connect(self.path) as db:
            old=db.execute("SELECT envelope FROM promotion_receipts WHERE gate='cost'").fetchone()[0]
            db.execute("UPDATE promotion_receipts SET envelope=? WHERE gate='cost'",('{"body":null,'+old[1:],))
        self.assertIn("cost",self.review()["missing"])
    def test_incomplete_trust(self):
        trust=dict(self.trust)
        del trust["tribunal"]
        self.assertEqual(self.review(trust=trust)["decision"],"BLOCKED")
    def test_duplicate_id(self):
        ids=dict(self.ids)
        ids["cost"]=ids["tests"]
        self.assertEqual(self.review(receipt_ids=ids)["decision"],"BLOCKED")
