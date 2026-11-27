import base64
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from governance.promotion_gate import REQUIRED_GATES
from governance.signed_promotion_receipts import canonical_receipt
from governance.prod_release_review import review

class ProdReview(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.artifact = root/"candidate.zip"
        self.artifact.write_bytes(b"synthetic candidate archive")
        self.evidence = root/"evidence.zip"
        self.config = {"artifact_id": 1, "evidence_artifact_id": 2, "candidate": {
            "company_id": "fixture", "engine_id": "FACT-001", "environment": "PROD",
            "version": "1", "commit": "a"*40, "artifact_sha256": hashlib.sha256(self.artifact.read_bytes()).hexdigest()},
            "trust": {}, "receipt_ids": {}}
        self.receipts = []
        for gate in REQUIRED_GATES:
            key = Ed25519PrivateKey.generate()
            issuer = "fixture:" + gate
            eid = "fixture-receipt:" + gate
            self.config["trust"][gate] = {"issuer": issuer, "public_key_hex": key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()}
            self.config["receipt_ids"][gate] = eid
            payload = gate.encode()
            body = {"schema": "cerebro.promotion.evidence.v1", "gate": gate,
                "candidate": dict(self.config["candidate"]), "evidence_id": eid, "payload_sha256": hashlib.sha256(payload).hexdigest(),
                "issuer": issuer, "observed_at": 100, "expires_at": 200, "result": "PASS"}
            self.receipts.append({"gate": gate, "evidence_id": eid, "payload_b64": base64.b64encode(payload).decode(),
                "envelope": {"body": body, "signature": key.sign(canonical_receipt(body)).hex()}})
        self.bundle()
    def bundle(self):
        with zipfile.ZipFile(self.evidence, "w") as z:
            z.writestr("receipts.json", json.dumps({"schema": "cerebro.prod.evidence.package.v1", "receipts": self.receipts}))
        self.config["evidence_sha256"] = hashlib.sha256(self.evidence.read_bytes()).hexdigest()
    def check(self, now=150):
        result = review(json.dumps(self.config), self.artifact, self.evidence, lambda: now)
        self.assertIs(result["deployment_authorized"], False)
        return result
    def test_complete_is_review_only(self):
        self.assertEqual(self.check()["decision"], "PROD_REVIEW_CANDIDATE")
    def test_wrong_artifact(self):
        self.artifact.write_bytes(b"wrong")
        self.assertEqual(self.check()["reason"], "ARCHIVE_DIGEST_MISMATCH")
    def test_expired(self):
        self.assertEqual(self.check(200)["decision"], "BLOCKED")
    def test_signature_tampering(self):
        self.receipts[0]["envelope"]["signature"] = "0"*128
        self.bundle()
        self.assertEqual(self.check()["decision"], "BLOCKED")
    def test_missing_receipt(self):
        self.receipts.pop()
        self.bundle()
        self.assertEqual(self.check()["decision"], "BLOCKED")
    def test_wrong_environment(self):
        self.config["candidate"]["environment"] = "PREPROD"
        self.assertEqual(self.check()["decision"], "BLOCKED")
    def test_no_config(self):
        self.assertEqual(review("{}", self.artifact, self.evidence, lambda: 150)["decision"], "BLOCKED")
    def test_duplicate_receipt(self):
        self.receipts[-1] = self.receipts[0]
        self.bundle()
        self.assertEqual(self.check()["decision"], "BLOCKED")

    def release_fixture(self):
        import sqlite3
        from governance.prod_release_authority import ReleaseTrust, canonical_approval
        key = Ed25519PrivateKey.generate()
        ledger = Path(self.tmp.name)/"release.sqlite"
        with sqlite3.connect(ledger) as db:
            db.execute("CREATE TABLE release_ledger_scope(environment TEXT NOT NULL)")
            db.execute("INSERT INTO release_ledger_scope VALUES('PROD')")
            db.execute("CREATE TABLE release_reservations(release_id TEXT PRIMARY KEY,target TEXT NOT NULL,company_id TEXT NOT NULL,engine_id TEXT NOT NULL,commit_sha TEXT NOT NULL,artifact_sha256 TEXT NOT NULL,evidence_sha256 TEXT NOT NULL,expires_at INTEGER NOT NULL,UNIQUE(target,company_id,engine_id,commit_sha,artifact_sha256))")
        trust = ReleaseTrust("fixture:release", key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw),
                             "fixture:target", (), "b"*64, ledger)
        body = {"schema":"cerebro.release.approval.v1","decision":"APPROVE","issuer":trust.issuer,
                "candidate":dict(self.config["candidate"]),"target":trust.target,"artifact_id":1,
                "evidence_artifact_id":2,"evidence_sha256":self.config["evidence_sha256"],
                "hold_resolution_sha256":trust.hold_resolution_sha256,"release_id":"fixture:release-001",
                "issued_at":120,"expires_at":180}
        def sign():
            return {"body":dict(body),"signature":key.sign(canonical_approval(body)).hex()}
        return trust, body, sign

    def authorize(self, trust, approval, now=150):
        from governance.prod_release_authority import authorize_release
        return authorize_release(json.dumps(self.config),self.artifact,self.evidence,approval,trust=trust,clock=lambda:now)

    def test_release_requires_approval(self):
        t,b,s=self.release_fixture()
        self.assertFalse(self.authorize(t,None)["deployment_authorized"])

    def test_release_valid_once(self):
        t,b,s=self.release_fixture()
        result=self.authorize(t,s())
        self.assertEqual(result["decision"],"RELEASE_RESERVED")
        self.assertTrue(result["deployment_authorized"])
        self.assertFalse(result["deployed"])
        self.assertEqual(self.authorize(t,s())["reason"],"RELEASE_ALREADY_RESERVED")
        b["release_id"]="fixture:release-002"
        self.assertEqual(self.authorize(t,s())["reason"],"RELEASE_ALREADY_RESERVED")

    def test_release_active_hold(self):
        from dataclasses import replace
        t,b,s=self.release_fixture()
        self.assertEqual(self.authorize(replace(t,active_holds=("OWNER_ADMISSION",)),s())["reason"],"ACTIVE_HOLDS")

    def test_release_tampered_signature(self):
        t,b,s=self.release_fixture()
        a=s(); a["signature"]="0"*128
        self.assertFalse(self.authorize(t,a)["deployment_authorized"])

    def test_release_wrong_scope(self):
        t,b,s=self.release_fixture()
        b["target"]="fixture:other"
        self.assertEqual(self.authorize(t,s())["reason"],"RELEASE_APPROVAL_SCOPE")

    def test_release_wrong_hold_resolution(self):
        t,b,s=self.release_fixture()
        b["hold_resolution_sha256"]="c"*64
        self.assertEqual(self.authorize(t,s())["reason"],"RELEASE_APPROVAL_SCOPE")

    def test_release_expired(self):
        t,b,s=self.release_fixture()
        self.assertEqual(self.authorize(t,s(),180)["reason"],"RELEASE_APPROVAL_EXPIRED")

    def test_release_independence(self):
        from dataclasses import replace
        t,b,s=self.release_fixture()
        gate=self.config["trust"]["tribunal"]
        self.assertEqual(self.authorize(replace(t,public_key=bytes.fromhex(gate["public_key_hex"])),s())["reason"],"RELEASE_AUTHORITY_NOT_INDEPENDENT")

    def test_release_missing_gate(self):
        t,b,s=self.release_fixture()
        self.receipts.pop(); self.bundle()
        b["evidence_sha256"]=self.config["evidence_sha256"]
        self.assertEqual(self.authorize(t,s())["reason"],"RELEASE_EVIDENCE_NOT_VERIFIED")

    def test_release_missing_ledger(self):
        from dataclasses import replace
        t,b,s=self.release_fixture()
        self.assertFalse(self.authorize(replace(t,ledger=t.ledger.parent/"absent.sqlite"),s())["deployment_authorized"])
        self.assertFalse((t.ledger.parent/"absent.sqlite").exists())
