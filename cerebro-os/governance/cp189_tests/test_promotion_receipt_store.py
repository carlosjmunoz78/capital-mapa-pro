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

    def stored_control(self, **kw):
        from gateway.control_plane_release import review_stored_control
        args=dict(candidate=self.candidate,receipt_ids=self.ids,store_path=self.path,
            trust=self.trust,clock=lambda:150,policy_decision="ALLOW",human_required=False,
            route_status="ROUTED",supervisor_state="GREEN",tribunal_approved=True,
            promotion_decision="PREPROD_GREEN",evidence_refs={g:"fixture:"+g for g in
                ("route","policy","supervisor","tribunal","promotion")})
        args.update(kw)
        return review_stored_control(**args)

    def test_composed_control_complete_remains_hold(self):
        before=self.path.read_bytes()
        r=self.stored_control()
        self.assertEqual(r["reason"],"SEPARATE_RELEASE_AUTHORITY_REQUIRED")
        self.assertEqual(r["review"]["decision"],"PREPROD_REVIEW_CANDIDATE")
        self.assertIs(r["deployment_authorized"],False)
        self.assertEqual(self.path.read_bytes(),before)

    def test_composed_control_missing_and_expiry(self):
        with sqlite3.connect(self.path) as db:
            db.execute("DELETE FROM promotion_receipts WHERE gate='backup'")
        r=self.stored_control()
        self.assertEqual(r["reason"],"VERIFIED_GATES_REQUIRED")
        self.assertIn("backup",r["review"]["missing"])
        self.assertEqual(len(self.stored_control(clock=lambda:200)["review"]["missing"]),12)

    def test_composed_control_wrong_environment(self):
        r=self.stored_control(candidate=replace(self.candidate,environment="PROD"),
            promotion_decision="PROD_CANDIDATE")
        self.assertEqual(r["reason"],"VERIFIED_GATES_REQUIRED")
        self.assertIs(r["deployment_authorized"],False)

    def test_composed_control_policy_and_supervisor(self):
        for kw in ({"policy_decision":"DENY"},{"supervisor_state":"RED"},
                   {"tribunal_approved":False},{"evidence_refs":{}}):
            r=self.stored_control(**kw)
            self.assertEqual(r["status"],"BLOCKED")
            self.assertIs(r["deployment_authorized"],False)
        self.assertEqual(self.stored_control(human_required=True)["status"],"HUMAN_REQUIRED")

    def test_composed_control_no_store_no_creation(self):
        missing=self.path.parent/"missing.sqlite"
        r=self.stored_control(store_path=missing)
        self.assertEqual(r["reason"],"VERIFIED_GATES_REQUIRED")
        self.assertFalse(missing.exists())
