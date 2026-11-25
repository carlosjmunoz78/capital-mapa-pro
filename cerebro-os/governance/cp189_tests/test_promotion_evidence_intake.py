import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from dataclasses import asdict,replace
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from governance.promotion_gate import REQUIRED_GATES
from governance.verified_promotion_gate import Candidate
from governance.signed_promotion_receipts import canonical_receipt
from governance.promotion_receipt_store import review_stored_candidate
from governance.promotion_evidence_intake import admit_receipt, admit_prod_receipt

class Intake(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"receipts.sqlite"
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE promotion_receipts(gate TEXT,evidence_id TEXT,payload BLOB,envelope TEXT,PRIMARY KEY(gate,evidence_id))")
        self.candidate=Candidate("fenix","FACT-001","PREPROD","1.1.0","a"*40,"b"*64)
        self.keys={g:Ed25519PrivateKey.generate() for g in REQUIRED_GATES}
        self.trust={g:("fixture:"+g,k.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)) for g,k in self.keys.items()}
    def args(self,gate="tests",eid=None):
        eid=eid or "fixture-receipt:"+gate
        payload=("synthetic:"+gate).encode()
        b=dict(schema="cerebro.promotion.evidence.v1",gate=gate,candidate=asdict(self.candidate),evidence_id=eid,payload_sha256=sha256(payload).hexdigest(),issuer=self.trust[gate][0],observed_at=100,expires_at=200,result="PASS")
        return dict(candidate=self.candidate,gate=gate,evidence_id=eid,payload=payload,envelope_json=json.dumps({"body":b,"signature":self.keys[gate].sign(canonical_receipt(b)).hex()}),store_path=self.path,trust=self.trust,clock=lambda:150)
    def count(self):
        with sqlite3.connect(self.path) as db:
            return db.execute("SELECT count(*) FROM promotion_receipts").fetchone()[0]
    def test_complete_pipeline_and_no_deploy_authority(self):
        ids={}
        for gate in REQUIRED_GATES:
            a=self.args(gate); ids[gate]=a["evidence_id"]
            r=admit_receipt(**a);self.assertEqual(r["status"],"ADMITTED");self.assertFalse(r["deployment_authorized"])
        self.assertEqual(self.count(),12)
        r=review_stored_candidate(candidate=self.candidate,receipt_ids=ids,store_path=self.path,trust=self.trust,clock=lambda:150,policy_decision="ALLOW",human_required=False)
        self.assertEqual(r["decision"],"PREPROD_REVIEW_CANDIDATE");self.assertFalse(r["deployment_authorized"])
    def test_exact_duplicate(self):
        a=self.args();self.assertEqual(admit_receipt(**a)["status"],"ADMITTED");self.assertEqual(admit_receipt(**a)["status"],"ALREADY_ADMITTED");self.assertEqual(self.count(),1)
    def test_concurrent_duplicate(self):
        a=self.args()
        with ThreadPoolExecutor(4) as e:
            outcomes=list(e.map(lambda _:admit_receipt(**a)["status"],range(4)))
        self.assertEqual(outcomes.count("ADMITTED"),1);self.assertEqual(outcomes.count("ALREADY_ADMITTED"),3);self.assertEqual(self.count(),1)
    def test_id_collision_across_gates(self):
        a=self.args();admit_receipt(**a)
        r=admit_receipt(**self.args("cost",a["evidence_id"]));self.assertEqual(r["reason"],"RECEIPT_ID_CONFLICT");self.assertEqual(self.count(),1)
    def test_tampering_and_foreign_candidate(self):
        a=self.args()
        for bad in [dict(payload=b"tampered"),dict(candidate=replace(self.candidate,company_id="other")),dict(candidate=replace(self.candidate,environment="PROD")),dict(clock=lambda:200),dict(envelope_json='{"body":null,'+a["envelope_json"][1:])]:
            self.assertEqual(admit_receipt(**{**a,**bad})["status"],"HOLD")
        self.assertEqual(self.count(),0)
    def test_untrusted_issuer(self):
        a=self.args();trust=dict(self.trust);trust["tests"]=("other",trust["tests"][1])
        self.assertEqual(admit_receipt(**{**a,"trust":trust})["status"],"HOLD");self.assertEqual(self.count(),0)
    def test_missing_store_no_creation(self):
        p=self.path.parent/"missing.sqlite";r=admit_receipt(**{**self.args(),"store_path":p})
        self.assertEqual(r["status"],"HOLD");self.assertFalse(p.exists())
    def test_incomplete_gate_set_still_blocks_review(self):
        a=self.args();admit_receipt(**a)
        r=review_stored_candidate(candidate=self.candidate,receipt_ids={g:"fixture-receipt:"+g for g in REQUIRED_GATES},store_path=self.path,trust=self.trust,clock=lambda:150,policy_decision="ALLOW",human_required=False)
        self.assertEqual(r["decision"],"BLOCKED");self.assertEqual(len(r["missing"]),11)


class ProdIntake(Intake):
    # Inherit the setup/receipt factory only, not the PREPROD assertions.
    def setUp(self):
        super().setUp()
        self.preprod_path=self.path
        self.path=self.path.parent/"prod.sqlite"
        self.candidate=replace(self.candidate,environment="PROD")
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE promotion_store_scope(environment TEXT NOT NULL)")
            db.execute("INSERT INTO promotion_store_scope VALUES('PROD')")
            db.execute("CREATE TABLE promotion_receipts(gate TEXT,evidence_id TEXT,payload BLOB,envelope TEXT,PRIMARY KEY(gate,evidence_id))")
    def test_complete_pipeline_and_no_deploy_authority(self):
        before=self.preprod_path.read_bytes()
        ids={}
        for gate in REQUIRED_GATES:
            a=self.args(gate); ids[gate]=a["evidence_id"]
            self.assertEqual(admit_prod_receipt(**a)["status"],"ADMITTED")
        r=review_stored_candidate(candidate=self.candidate,receipt_ids=ids,store_path=self.path,trust=self.trust,clock=lambda:150,policy_decision="ALLOW",human_required=False)
        self.assertEqual(r["decision"],"PROD_REVIEW_CANDIDATE")
        self.assertFalse(r["deployment_authorized"])
        self.assertEqual(self.count(),12)
        self.assertEqual(self.preprod_path.read_bytes(),before)
    def test_exact_duplicate(self):
        a=self.args();self.assertEqual(admit_prod_receipt(**a)["status"],"ADMITTED");self.assertEqual(admit_prod_receipt(**a)["status"],"ALREADY_ADMITTED");self.assertEqual(self.count(),1)
    def test_concurrent_duplicate(self):
        a=self.args()
        with ThreadPoolExecutor(4) as e:
            outcomes=list(e.map(lambda _:admit_prod_receipt(**a)["status"],range(4)))
        self.assertEqual(outcomes.count("ADMITTED"),1);self.assertEqual(outcomes.count("ALREADY_ADMITTED"),3);self.assertEqual(self.count(),1)
    def test_id_collision_across_gates(self):
        a=self.args();admit_prod_receipt(**a)
        self.assertEqual(admit_prod_receipt(**self.args("cost",a["evidence_id"]))["reason"],"RECEIPT_ID_CONFLICT")
        self.assertEqual(self.count(),1)
    def test_tampering_and_foreign_candidate(self):
        a=self.args()
        for bad in [dict(payload=b"tampered"),dict(candidate=replace(self.candidate,company_id="other")),dict(candidate=replace(self.candidate,environment="PREPROD")),dict(clock=lambda:200),dict(envelope_json='{"body":null,'+a["envelope_json"][1:])]:
            self.assertEqual(admit_prod_receipt(**{**a,**bad})["status"],"HOLD")
        self.assertEqual(self.count(),0)
    def test_untrusted_issuer(self):
        a=self.args();trust=dict(self.trust);trust["tests"]=("other",trust["tests"][1])
        self.assertEqual(admit_prod_receipt(**{**a,"trust":trust})["status"],"HOLD");self.assertEqual(self.count(),0)
    def test_missing_store_no_creation(self):
        p=self.path.parent/"missing.sqlite";r=admit_prod_receipt(**{**self.args(),"store_path":p})
        self.assertEqual(r["status"],"HOLD");self.assertFalse(p.exists())
    def test_incomplete_gate_set_still_blocks_review(self):
        admit_prod_receipt(**self.args())
        r=review_stored_candidate(candidate=self.candidate,receipt_ids={g:"fixture-receipt:"+g for g in REQUIRED_GATES},store_path=self.path,trust=self.trust,clock=lambda:150,policy_decision="ALLOW",human_required=False)
        self.assertEqual(r["decision"],"BLOCKED");self.assertEqual(len(r["missing"]),11)
    def test_prod_intake_cannot_write_legacy_preprod_store(self):
        before=self.preprod_path.read_bytes()
        self.assertEqual(admit_prod_receipt(**{**self.args(),"store_path":self.preprod_path})["reason"],"STORE_SCOPE_DENIED")
        self.assertEqual(self.preprod_path.read_bytes(),before)
    def test_preprod_intake_cannot_write_prod_store(self):
        self.candidate=replace(self.candidate,environment="PREPROD")
        self.assertEqual(admit_receipt(**self.args())["reason"],"STORE_SCOPE_DENIED")
        self.assertEqual(self.count(),0)
