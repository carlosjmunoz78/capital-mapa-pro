import hashlib
import hmac
import json
import secrets
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import importlib.util

SPEC=importlib.util.spec_from_file_location(
    "remote_read_proof_cp82", ROOT/"gateway"/"remote_read_proof_cp82.py")
CP82=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CP82)
assess_live_observation=CP82.assess_live_observation
verify_private_read_pair=CP82.verify_private_read_pair
SCHEMA=CP82.SCHEMA
CAPABILITY=CP82.CAPABILITY

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

class AuthorizedPrivateReadCP131Tests(unittest.TestCase):
    mac = RemotePrivateProofCP82Tests.mac
    def setUp(self):
        RemotePrivateProofCP82Tests.setUp(self)
        self.principal = "jarvis-lab-service-fixture"
        self.issuer = "iam-lab-issuer-fixture"
        self.ref = "policy://lab-fixture/0001"
        for item in (self.jarvis, self.fact):
            item.update(principal_id=self.principal, policy_receipt_ref=self.ref)
        self.store[self.request] = dict(self.fact)
        self.grant = {"policy_receipt_ref": self.ref, "issuer_id": self.issuer,
                      "principal_id": self.principal, "company_id": self.company,
                      "request_id": self.request, "engine_id": "FACT-001", "environment": "LAB",
                      "version": "1.0.0", "capability": CAPABILITY, "decision": "ALLOW_READ_ONLY",
                      "verified": True, "active": True, "revoked": False, "read_only": True,
                      "external_mutation_allowed": False, "cost_ceiling_eur": 0,
                      "issued_at_epoch": self.now - 30, "expires_at_epoch": self.now + 300}

    def authorized(self, **kwargs):
        args = {"jarvis": self.jarvis, "fact": self.fact,
                "jarvis_signature": self.mac(self.jarvis, self.key_j),
                "fact_signature": self.mac(self.fact, self.key_f),
                "jarvis_key": self.key_j, "fact_key": self.key_f,
                "company_id": self.company, "request_id": self.request, "now_epoch": self.now,
                "persisted_fact_reader": self.store.get, "trusted_grant_reader": lambda ref: self.grant if ref == self.ref else None,
                "expected_principal": self.principal, "expected_issuer": self.issuer,
                "canonical_company_id": self.company}
        args.update(kwargs)
        return CP82.verify_authorized_private_read(**args)

    def test_cp131_valid_fixture_never_promotes(self):
        out = self.authorized()
        self.assertEqual(out["status"], "VERIFIED_AUTHORIZED_PAIR")
        self.assertTrue(out["iam_grant_verified"])
        self.assertFalse(out["promotion_allowed"])

    def test_cp131_missing_reader_or_grant(self):
        for reader in (None, lambda ref: None):
            with self.subTest(reader=reader), self.assertRaises(PermissionError):
                self.authorized(trusted_grant_reader=reader)

    def test_cp131_wrong_tenant_issuer_or_principal(self):
        for field, value in (("company_id", "aion"), ("issuer_id", "untrusted"), ("principal_id", "other"),
                             ("request_id", "wrong-request"), ("capability", "FACT.WRITE"), ("environment", "PROD")):
            with self.subTest(field=field), self.assertRaisesRegex(PermissionError, "GRANT_SCOPE"):
                self.authorized(trusted_grant_reader=lambda ref: {**self.grant, field: value})
        with self.assertRaisesRegex(PermissionError, "IDENTITY_SCOPE"):
            self.authorized(canonical_company_id="fenix")

    def test_cp131_revoked_unverified_or_mutative(self):
        for field, value in (("revoked", True), ("verified", False), ("active", False), ("read_only", False),
                             ("external_mutation_allowed", True), ("cost_ceiling_eur", 1)):
            with self.subTest(field=field), self.assertRaisesRegex(PermissionError, "GRANT_POLICY"):
                self.authorized(trusted_grant_reader=lambda ref: {**self.grant, field: value})

    def test_cp131_lifetime_and_receipt_age(self):
        for start, end in ((self.now-901, self.now+1), (self.now-10, self.now),
                           (self.now+1, self.now+100), (self.now-1, self.now+900)):
            with self.subTest(start=start, end=end), self.assertRaisesRegex(PermissionError, "GRANT_LIFETIME"):
                self.authorized(trusted_grant_reader=lambda ref: {**self.grant, "issued_at_epoch": start, "expires_at_epoch": end})
        with self.assertRaisesRegex(ValueError, "RECEIPT_AGE"):
            self.authorized(max_age_s=901)

    def test_cp131_fact_must_bind_same_grant(self):
        self.fact["policy_receipt_ref"] = "policy://other-grant"
        self.store[self.request] = dict(self.fact)
        with self.assertRaisesRegex(PermissionError, "RECEIPT_GRANT_BINDING"):
            self.authorized()


    def test_cp149_authorized_reader_checks_iam_before_storage(self):
        calls = []
        def grant_reader(ref):
            calls.append(("IAM", ref))
            return self.grant
        def fact_reader(request_id):
            calls.append(("FACT", request_id))
            return self.store.get(request_id)
        out = self.authorized(trusted_grant_reader=grant_reader, persisted_fact_reader=fact_reader)
        self.assertEqual(out["status"], "VERIFIED_AUTHORIZED_PAIR")
        self.assertFalse(out["promotion_allowed"])
        self.assertEqual(calls, [("IAM", self.ref), ("FACT", self.request)])

    def test_cp149_denied_grants_never_touch_fact_storage(self):
        invalid_grants = (
            None, {}, {**self.grant, "company_id": "aion"},
            {**self.grant, "issuer_id": "other"}, {**self.grant, "principal_id": "other"},
            {**self.grant, "capability": "FACT.WRITE"}, {**self.grant, "environment": "PROD"},
            {**self.grant, "revoked": True}, {**self.grant, "active": False},
            {**self.grant, "verified": False}, {**self.grant, "cost_ceiling_eur": 1},
            {**self.grant, "external_mutation_allowed": True},
            {**self.grant, "expires_at_epoch": self.now},
            {**self.grant, "issued_at_epoch": self.now - 901},
        )
        for grant in invalid_grants:
            with self.subTest(grant=grant):
                calls = []
                def fact_reader(request_id):
                    calls.append(request_id)
                    return self.store.get(request_id)
                with self.assertRaises(PermissionError):
                    self.authorized(trusted_grant_reader=lambda _: grant, persisted_fact_reader=fact_reader)
                self.assertEqual(calls, [])

    def test_cp149_iam_transport_failure_never_touches_fact_storage(self):
        calls = []
        def unavailable(_):
            raise RuntimeError("IAM unavailable")
        def fact_reader(request_id):
            calls.append(request_id)
            return self.store.get(request_id)
        with self.assertRaisesRegex(RuntimeError, "IAM unavailable"):
            self.authorized(trusted_grant_reader=unavailable, persisted_fact_reader=fact_reader)
        self.assertEqual(calls, [])

    def test_cp149_invalid_mac_never_touches_iam_or_fact_storage(self):
        for field in ("jarvis_signature", "fact_signature"):
            with self.subTest(field=field):
                calls = []
                def grant_reader(ref):
                    calls.append("IAM")
                    return self.grant
                def fact_reader(request_id):
                    calls.append("FACT")
                    return self.store.get(request_id)
                with self.assertRaisesRegex(PermissionError, "MAC invalid"):
                    self.authorized(trusted_grant_reader=grant_reader, persisted_fact_reader=fact_reader,
                                    **{field: "b" * 64})
                self.assertEqual(calls, [])

    def test_cp149_receipt_principal_or_reference_mismatch_never_touches_storage(self):
        for field, value in (("principal_id", "different"), ("policy_receipt_ref", "policy://other-grant")):
            with self.subTest(field=field):
                original = self.fact[field]
                self.fact[field] = value
                self.store[self.request] = dict(self.fact)
                calls = []
                def fact_reader(request_id):
                    calls.append(request_id)
                    return self.store.get(request_id)
                with self.assertRaisesRegex(PermissionError, "RECEIPT_GRANT_BINDING"):
                    self.authorized(persisted_fact_reader=fact_reader)
                self.assertEqual(calls, [])
                self.fact[field] = original
                self.store[self.request] = dict(self.fact)

    def test_cp149_authorized_grant_cannot_replace_independent_fact_receipt(self):
        with self.assertRaisesRegex(PermissionError, "persisted FACT"):
            self.authorized(persisted_fact_reader=lambda _: None)


if __name__=="__main__":
    unittest.main()
