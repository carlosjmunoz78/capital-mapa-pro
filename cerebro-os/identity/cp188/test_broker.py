import dataclasses, json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from broker import *

class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"fixture.json"
        self.cred={"type":"external_account","audience":AUDIENCE,"service_account_impersonation_url":IMPERSONATION,"token_url":"https://sts.googleapis.com/v1/token"}
        self.path.write_text(json.dumps(self.cred))
        self.env={"GITHUB_ACTIONS":"true","GITHUB_REPOSITORY":EXPECTED_REPO,"GITHUB_REF":EXPECTED_REF,
                  "GOOGLE_APPLICATION_CREDENTIALS":str(self.path),"CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE":str(self.path)}
        self.calls=[]
        self.account=ACCOUNT
        self.ingress="internal"
        self.error=False

    def fake(self, argv, **kwargs):
        self.calls.append(argv)
        if self.error:
            return SimpleNamespace(returncode=1,stdout="untrusted",stderr="secret-looking-error")
        result=([{"account":self.account}] if "auth" in argv else
                {"metadata":{"name":SERVICE,"annotations":{"run.googleapis.com/ingress":self.ingress}},
                 "status":{"traffic":[{"percent":100,"revisionName":"candidate"}]}})
        return SimpleNamespace(returncode=0,stdout=json.dumps(result),stderr="")

    def broker(self):
        return ScopedCredentialBroker(providers={FORGE:ForgeFederatedRead(env=self.env,run=self.fake)})

    def test_scoped_operation(self):
        r=self.broker().execute(FORGE)
        self.assertEqual(r["status"],"CP188_FEDERATED_READ_VERIFIED")
        self.assertFalse(r["credential_value_exposed"])
        self.assertEqual(len(self.calls),2)
        self.assertIn("--project="+PROJECT,self.calls[1])
        self.assertIn(SERVICE,self.calls[1])

    def test_cross_company_engine_version_account_operation_and_prod(self):
        for field,value in (("company_id","foreign"),("engine_id","OTHER"),("version","2.0.0"),("account_id","other"),("operation","WRITE"),("environment","PROD")):
            with self.assertRaises(PermissionError):
                self.broker().execute(dataclasses.replace(FORGE,**{field:value}))
        self.assertFalse(self.calls)

    def test_wrong_branch(self):
        self.env["GITHUB_REF"]="refs/heads/main"
        with self.assertRaisesRegex(PermissionError,"RUNTIME_DENIED"):
            self.broker().execute(FORGE)
        self.assertFalse(self.calls)

    def test_static_key_rejected(self):
        self.path.write_text(json.dumps({"type":"service_account","private_key":"fixture"}))
        with self.assertRaisesRegex(PermissionError,"REFERENCE_DENIED"):
            self.broker().execute(FORGE)
        self.assertFalse(self.calls)

    def test_wrong_provider_audience(self):
        self.cred["audience"]="other"
        self.path.write_text(json.dumps(self.cred))
        with self.assertRaisesRegex(PermissionError,"REFERENCE_DENIED"):
            self.broker().execute(FORGE)

    def test_wrong_account(self):
        self.account="other"
        with self.assertRaisesRegex(PermissionError,"ACCOUNT_DENIED"):
            self.broker().execute(FORGE)
        self.assertEqual(len(self.calls),1)

    def test_public_target_denied(self):
        self.ingress="all"
        with self.assertRaisesRegex(PermissionError,"TARGET_DENIED"):
            self.broker().execute(FORGE)

    def test_failure_sanitized(self):
        self.error=True
        with self.assertRaisesRegex(PermissionError,"^PROVIDER_OPERATION_DENIED$"):
            self.broker().execute(FORGE)

class ProdCatalogBrokerTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.auth_calls = []

    def provider(self):
        self.calls.append("catalog")
        return {"status": "TEST_ONLY"}

    def allow(self, scope):
        self.auth_calls.append(scope)
        return True

    def test_missing_authority_fails_closed(self):
        broker = ScopedCredentialBroker(providers={FACT_CATALOG_PROD: self.provider})
        with self.assertRaisesRegex(PermissionError, "PROD_AUTHORITY_REQUIRED"):
            broker.execute(FACT_CATALOG_PROD)
        self.assertEqual(self.calls, [])

    def test_only_exact_scope_with_trusted_authority(self):
        broker = ScopedCredentialBroker(providers={FACT_CATALOG_PROD: self.provider},
                                         prod_authorizer=self.allow)
        for field, value in (("company_id", "other"), ("engine_id", "OTHER"),
                             ("account_id", "other"), ("version", "2.0.0"),
                             ("operation", "WRITE")):
            with self.assertRaises(PermissionError):
                broker.execute(dataclasses.replace(FACT_CATALOG_PROD, **{field: value}))
        self.assertEqual(self.calls, [])
        self.assertEqual(self.auth_calls, [])
        self.assertEqual(broker.execute(FACT_CATALOG_PROD), {"status": "TEST_ONLY"})
        self.assertEqual(self.calls, ["catalog"])
        self.assertEqual(self.auth_calls, [FACT_CATALOG_PROD])

    def test_denied_non_boolean_and_failed_authority(self):
        def broken(scope):
            raise RuntimeError("sensitive")
        for checker in (lambda scope: False, lambda scope: 1, broken):
            broker = ScopedCredentialBroker(providers={FACT_CATALOG_PROD: self.provider},
                                             prod_authorizer=checker)
            with self.assertRaisesRegex(PermissionError, "^PROD_AUTHORITY_DENIED$"):
                broker.execute(FACT_CATALOG_PROD)
        self.assertEqual(self.calls, [])

    def test_no_fallback_and_no_forge_prod(self):
        broker = ScopedCredentialBroker(providers={FORGE: self.provider},
                                         prod_authorizer=self.allow)
        with self.assertRaises(PermissionError):
            broker.execute(FACT_CATALOG_PROD)
        with self.assertRaises(PermissionError):
            broker.execute(dataclasses.replace(FORGE, environment="PROD"))
        self.assertEqual(self.calls, [])

if __name__=="__main__":
    unittest.main()
