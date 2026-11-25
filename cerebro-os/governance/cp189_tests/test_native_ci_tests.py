import copy
import unittest
from datetime import datetime,timezone
from unittest.mock import patch
from governance import native_ci_tests as n

class NativeTests(unittest.TestCase):
    def fixture(self):
        cert={"issuer":"https://token.actions.githubusercontent.com",
            "subjectAlternativeName":"https://github.com/"+n.WORKFLOW+"@refs/pull/290/merge",
            "buildSignerURI":"https://github.com/"+n.WORKFLOW+"@refs/pull/290/merge",
            "buildSignerDigest":n.COMMIT,"sourceRepositoryDigest":n.COMMIT,
            "sourceRepositoryIdentifier":"1139292249","sourceRepositoryOwnerIdentifier":"130542695",
            "sourceRepositoryRef":"refs/pull/290/merge","runnerEnvironment":"github-hosted",
            "buildTrigger":"pull_request","runInvocationURI":"https://github.com/"+n.REPO+"/actions/runs/45596144769/attempts/1"}
        return [{"verificationResult":{"signature":{"certificate":cert},
            "statement":{"_type":"https://in-toto.io/Statement/v1","subject":[{"name":"candidate.zip","digest":{"sha256":n.ARTIFACT}}],
            "predicateType":n.PREDICATE,"predicate":copy.deepcopy(n.EXPECTED)},
            "verifiedTimestamps":[{"type":"Tlog","uri":"https://rekor.sigstore.dev","timestamp":"2026-11-25T10:34:07Z"}]}}]
    def now(self): return int(datetime(2026,11,25,10,35,tzinfo=timezone.utc).timestamp())
    def test_pinned_fixture(self):
        p,r=n._verify_output(self.fixture(),self.now())
        self.assertEqual(r.candidate,n.CANDIDATE);self.assertEqual(r.gate,"tests")
    def test_scope_and_digest(self):
        for k,v in [("environment","PROD"),("promotion_authorized",True),("artifact_sha256","0"*64),("gate","tribunal"),("module_count",True)]:
            x=self.fixture();x[0]["verificationResult"]["statement"]["predicate"][k]=v
            with self.assertRaises(ValueError):n._verify_output(x,self.now())
    def test_issuer_and_workflow(self):
        for k,v in [("issuer","other"),("sourceRepositoryIdentifier","123"),("buildSignerDigest","a"*40),("runnerEnvironment","self-hosted"),("sourceRepositoryRef","refs/heads/main")]:
            x=self.fixture();x[0]["verificationResult"]["signature"]["certificate"][k]=v
            with self.assertRaises(ValueError):n._verify_output(x,self.now())
    def test_expiry_and_duplicate(self):
        for x,t in [(self.fixture(),self.now()+3600),(self.fixture()*2,self.now()),(self.fixture(),self.now()-3600)]:
            with self.assertRaises(ValueError):n._verify_output(x,t)
    def test_partial_gate_blocks_release(self):
        p,r=n._verify_output(self.fixture(),self.now())
        with patch.object(n,"verify_native_tests",return_value=(p,r)),patch.object(n.time,"time",return_value=self.now()):
            x=n.review_native_tests("fixture")
        self.assertEqual(x["review"]["decision"],"BLOCKED")
        self.assertEqual(len(x["review"]["missing"]),11)
        self.assertFalse(x["review"]["deployment_authorized"])
