import hashlib
import hmac
import json
import secrets
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gateway.remote_read_proof_cp82 import (
    assess_live_observation,verify_private_read_pair,SCHEMA,CAPABILITY
)

class RemotePrivateProofCP82Tests(unittest.TestCase):
    def setUp(self):
        self.now=1795395000
        self.company="fenix-capital"
        self.request="cp82-lab-read-0001"
        self.key_j=secrets.token_bytes(32)
        self.key_f=secrets.token_bytes(32)
        scope={"schema":SCHEMA,"request_id":self.request,"company_id":self.company,
               "engine_id":"FACT-001","environment":"LAB","version":"1.0.0",
               "capability":CAPABILITY,"read_only":True,"external_mutation_allowed":False,
               "cost_ceiling_eur":0,"emitted_at_epoch":self.now}
        self.jarvis={**scope,"origin":"JARVIS","target":"FACT-001",
                     "owner_access_verified":True,"iam_policy":"ALLOW_READ_ONLY",
                     "policy_receipt_ref":"policy://local-test"}
        self.fact={**scope,"origin":"FACT-001","target":"JARVIS",
                   "status":"COMPLETED","result_sha256":"a"*64}
        self.store={self.request:dict(self.fact)}
    def mac(self,payload,key):
        raw=json.dumps(payload,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
        return hmac.new(key,raw,hashlib.sha256).hexdigest()
    def verify(self,**kwargs):
        kw={"jarvis":self.jarvis,"fact":self.fact,
            "jarvis_signature":self.mac(self.jarvis,self.key_j),
            "fact_signature":self.mac(self.fact,self.key_f),
            "jarvis_key":self.key_j,"fact_key":self.key_f,
            "company_id":self.company,"request_id":self.request,"now_epoch":self.now,
            "persisted_fact_reader":self.store.get}
        kw.update(kwargs)
        return verify_private_read_pair(**kw)
    def test_independent_observations_never_count_as_e2e(self):
        evidence={"access":{"allowed":True,"owner_match":True},
                  "fact":{"company_id":self.company,"engine_id":"FACT-001",
                          "environment":"LAB","operation":"providers.five.inventory.read",
                          "completed_jobs":12},
                  "gateway":{"jarvis_fact_binding_verified":False,
                             "enterprise_iam_verified":False,
                             "correlated_signed_receipt_verified":False}}
        out=assess_live_observation(evidence)
        self.assertEqual(out["status"],"BLOCKED")
        self.assertFalse(out["jarvis_fact_e2e_verified"])
        self.assertTrue(out["source_owner_access_verified"])
        self.assertTrue(out["fact_d1_inventory_verified"])
        self.assertIn("JARVIS_FACT_SERVICE_BINDING_MISSING",out["missing"])
    def test_promotional_booleans_cannot_override_missing_remote_reader(self):
        report=assess_live_observation({"access":{"allowed":True,"owner_match":True},
               "fact":{"company_id":self.company,"engine_id":"FACT-001",
                       "environment":"LAB","operation":"providers.five.inventory.read",
                       "completed_jobs":12},
               "gateway":{"jarvis_fact_binding_verified":True,
                          "enterprise_iam_verified":True,
                          "correlated_signed_receipt_verified":True}})
        self.assertFalse(report["promotion_allowed"])
        self.assertFalse(report["jarvis_fact_e2e_verified"])
        self.assertIn("LIVE_E2E_RECEIPT_RETRIEVAL_REQUIRED",report["missing"])
    def test_synthetic_signed_pair_passes_but_no_promotion(self):
        out=self.verify()
        self.assertEqual(out["status"],"VERIFIED_PAIR")
        self.assertFalse(out["promotion_allowed"])
        self.assertFalse(out["production_activation_allowed"])
    def test_cross_tenant_replay_is_denied(self):
        self.fact["company_id"]="aion"
        with self.assertRaisesRegex(ValueError,"company mismatch"):
            self.verify()
    def test_wrong_correlation_denied(self):
        self.fact["request_id"]="cp82-other-request"
        with self.assertRaisesRegex(ValueError,"correlation mismatch"):
            self.verify()
    def test_stale_timestamp_denied(self):
        self.fact["emitted_at_epoch"]=self.now-1000
        with self.assertRaisesRegex(ValueError,"freshness denied"):
            self.verify()
    def test_future_timestamp_denied(self):
        self.jarvis["emitted_at_epoch"]=self.now+31
        with self.assertRaisesRegex(ValueError,"freshness denied"):
            self.verify()
    def test_independent_fact_mac_mandatory(self):
        with self.assertRaisesRegex(PermissionError,"FACT receipt MAC invalid"):
            self.verify(fact_signature="b"*64)
    def test_independent_jarvis_mac_mandatory(self):
        with self.assertRaisesRegex(PermissionError,"JARVIS receipt MAC invalid"):
            self.verify(jarvis_signature="b"*64)
    def test_missing_persisted_receipt_denied(self):
        with self.assertRaisesRegex(PermissionError,"persisted FACT"):
            self.verify(persisted_fact_reader=lambda _:None)
    def test_persisted_receipt_conflict_denied(self):
        with self.assertRaisesRegex(PermissionError,"persisted FACT"):
            self.verify(persisted_fact_reader=lambda _:{"status":"COMPLETED"})
    def test_raw_credential_in_payload_denied(self):
        self.fact["token"]="not-a-token"
        with self.assertRaisesRegex(ValueError,"raw credentials forbidden"):
            self.verify()
    def test_duplicate_signing_keys_denied(self):
        with self.assertRaisesRegex(ValueError,"distinct service keys required"):
            self.verify(fact_key=self.key_j)
    def test_wrong_policy_denied(self):
        self.jarvis["iam_policy"]="ALLOW_EXECUTION"
        with self.assertRaisesRegex(ValueError,"identity/policy proof"):
            self.verify()
    def test_prod_environment_denied(self):
        self.fact["environment"]="PROD"
        with self.assertRaisesRegex(ValueError,"environment denied"):
            self.verify()
    def test_nonzero_cost_denied(self):
        self.fact["cost_ceiling_eur"]=0.01
        with self.assertRaisesRegex(ValueError,"cost ceiling"):
            self.verify()
    def test_mutation_request_denied(self):
        self.jarvis["external_mutation_allowed"]=True
        with self.assertRaisesRegex(ValueError,"mutation forbidden"):
            self.verify()
    def test_invalid_fact_digest_denied(self):
        self.fact["result_sha256"]="not-a-digest"
        with self.assertRaisesRegex(ValueError,"FACT read receipt"):
            self.verify()
    def test_distinct_version_denied(self):
        self.fact["version"]="1.0.1"
        with self.assertRaisesRegex(ValueError,"version mismatch"):
            self.verify()
    def test_fails_closed_without_reader(self):
        with self.assertRaisesRegex(ValueError,"independent persistent reader"):
            self.verify(persisted_fact_reader=None)

if __name__=="__main__":
    unittest.main()
