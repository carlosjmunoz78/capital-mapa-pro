import hashlib, hmac, json, sys, unittest
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"factory"))
from ums001_visual_qa_gate import assess_private_asset,require_reuse_approval,REQUIRED_CHECKS,REVIEWER_ID
B2C="6b4b1596ec87efd30f4d7ac677e19514a10f6896b22587dddcec06a23c8c2791"
B2B="c227a0723d89a2ff8292d709bd171aa617a8cfb27dbeb64ea508df23c87dfc18"
KEY=b"LOCAL_TEST_ONLY_fake_key_NOT_A_REAL_SECRET_123456"
def p(sha="a"*64):
    return dict(asset_sha256=sha,company_id="fenix",engine_id="CEREBRO-NEWS-001",request_id="UMS001-LAB-NEWS001-B2C-20261117-03",environment="LAB")
def signed(sha="a"*64,checks=None,confidence=.95):
    payload=dict(p(sha),reviewer_id=REVIEWER_ID,reviewed_at=datetime.now(timezone.utc).isoformat(),checks=checks if checks is not None else {x:True for x in REQUIRED_CHECKS},confidence=confidence)
    sig=hmac.new(KEY,json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode(),hashlib.sha256).hexdigest()
    return {"payload":payload,"hmac_sha256":sig}
class TestUMS001VisualGate(unittest.TestCase):
    def test_known_rejected_b2c(self):
        x=assess_private_asset(**p(B2C));self.assertEqual(x["qa_state"],"REJECTED_VISUAL");self.assertFalse(x["reuse_allowed"])
        with self.assertRaises(PermissionError):require_reuse_approval(x)
    def test_known_rejected_b2b(self):
        x=assess_private_asset(**p(B2B));self.assertEqual(x["qa_state"],"REJECTED_VISUAL")
    def test_no_review_blocks(self):
        x=assess_private_asset(**p());self.assertEqual(x["qa_state"],"QA_HOLD");self.assertFalse(x["publish_authorized"])
    def test_fake_claim_blocks(self):
        x=assess_private_asset(**p(),attestation={"passed":True},reviewer_hmac_key=KEY);self.assertEqual(x["qa_state"],"QA_HOLD")
    def test_no_key_blocks(self):
        x=assess_private_asset(**p(),attestation=signed());self.assertEqual(x["qa_state"],"QA_HOLD")
    def test_changed_signature_blocks(self):
        s=signed();s["payload"]["company_id"]="other"
        x=assess_private_asset(**p(),attestation=s,reviewer_hmac_key=KEY);self.assertEqual(x["qa_reason_codes"],["INVALID_SIGNATURE"])
    def test_wrong_identity_blocks(self):
        x=assess_private_asset(**dict(p(),company_id="other"),attestation=signed(),reviewer_hmac_key=KEY)
        self.assertEqual(x["qa_reason_codes"],["REVIEW_IDENTITY_MISMATCH"])
    def test_wrong_sha_blocks(self):
        x=assess_private_asset(**p("b"*64),attestation=signed(),reviewer_hmac_key=KEY)
        self.assertEqual(x["qa_reason_codes"],["REVIEW_IDENTITY_MISMATCH"])
    def test_missing_checks_blocks(self):
        checks={x:True for x in REQUIRED_CHECKS};checks.pop("limbs_connected")
        x=assess_private_asset(**p(),attestation=signed(checks=checks),reviewer_hmac_key=KEY)
        self.assertEqual(x["qa_reason_codes"],["INCOMPLETE_VISION_CHECKS"])
    def test_bad_anatomy_blocks(self):
        checks={x:True for x in REQUIRED_CHECKS};checks["limbs_connected"]=False
        x=assess_private_asset(**p(),attestation=signed(checks=checks),reviewer_hmac_key=KEY)
        self.assertEqual(x["qa_state"],"REJECTED_VISUAL")
    def test_bad_text_blocks(self):
        checks={x:True for x in REQUIRED_CHECKS};checks["no_fake_text"]=False
        x=assess_private_asset(**p(),attestation=signed(checks=checks),reviewer_hmac_key=KEY)
        self.assertFalse(x["reuse_allowed"])
    def test_low_confidence_blocks(self):
        x=assess_private_asset(**p(),attestation=signed(confidence=.60),reviewer_hmac_key=KEY)
        self.assertEqual(x["qa_reason_codes"],["LOW_CONFIDENCE"])
    def test_blacklist_overrides_perfect_review(self):
        x=assess_private_asset(**p(B2C),attestation=signed(sha=B2C),reviewer_hmac_key=KEY)
        self.assertEqual(x["qa_state"],"REJECTED_VISUAL")
    def test_valid_signed_qa_only_enables_reuse(self):
        x=assess_private_asset(**p(),attestation=signed(),reviewer_hmac_key=KEY)
        self.assertTrue(x["reuse_allowed"]);self.assertFalse(x["publish_authorized"])
        require_reuse_approval(x)
    def test_empty_receipt_denied(self):
        with self.assertRaises(PermissionError):require_reuse_approval({})
    def test_invalid_sha_denied(self):
        x=assess_private_asset(**p("invalid"));self.assertEqual(x["qa_state"],"QA_HOLD")
if __name__=="__main__":unittest.main()
