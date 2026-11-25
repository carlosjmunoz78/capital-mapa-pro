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
