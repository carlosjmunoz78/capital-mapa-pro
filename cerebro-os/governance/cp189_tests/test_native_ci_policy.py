import copy
from dataclasses import replace
from datetime import datetime,timezone
import unittest
from unittest.mock import patch
from governance import native_ci_policy as n

class RecurringPolicy(unittest.TestCase):
    def setUp(self):
        self.p=n.BuildPolicy("a"*40,"b"*40,123,1,456,"c"*64)
        self.now=int(datetime(2026,11,25,10,35,tzinfo=timezone.utc).timestamp())
    def fixture(self,p=None):
        p=p or self.p
        uri="https://github.com/"+n.WORKFLOW+"@refs/pull/290/merge"
        cert={"issuer":"https://token.actions.githubusercontent.com","subjectAlternativeName":uri,
            "buildSignerURI":uri,"buildSignerDigest":p.commit,"sourceRepositoryDigest":p.commit,
            "sourceRepositoryIdentifier":"1139292249","sourceRepositoryOwnerIdentifier":"130542695",
            "sourceRepositoryRef":"refs/pull/290/merge","runnerEnvironment":"github-hosted","buildTrigger":"pull_request",
            "runInvocationURI":f"https://github.com/{n.REPO}/actions/runs/{p.run_id}/attempts/{p.attempt}"}
        return [{"verificationResult":{"signature":{"certificate":cert},"statement":{
          "_type":"https://in-toto.io/Statement/v1","predicateType":n.PREDICATE,"predicate":p.predicate,
          "subject":[{"name":"candidate.zip","digest":{"sha256":p.artifact_sha256}}]},
          "verifiedTimestamps":[{"type":"Tlog","uri":"https://rekor.sigstore.dev","timestamp":"2026-11-25T10:34:07Z"}]}}]
    def test_distinct_candidates(self):
        for p in [self.p,replace(self.p,commit="d"*40,run_id=124,artifact_id=457,attempt=2)]:
            _,r=n._verified_receipt(self.fixture(p),p,self.now)
            self.assertEqual(r.candidate,p.candidate);self.assertEqual(r.evidence_id,p.evidence_id)
    def test_cross_candidate(self):
        for p in [replace(self.p,head="d"*40),replace(self.p,attempt=2),replace(self.p,run_id=124),replace(self.p,artifact_id=457),replace(self.p,artifact_sha256="e"*64)]:
            with self.assertRaises(ValueError):n._verified_receipt(self.fixture(),p,self.now)
    def test_bad_policy(self):
        for k,v in [("commit","bad"),("attempt",True),("artifact_id",0),("artifact_sha256","bad")]:
            with self.assertRaises(ValueError):replace(self.p,**{k:v})
    def test_certificate(self):
        for k,v in [("sourceRepositoryIdentifier","9"),("runnerEnvironment","self-hosted"),("sourceRepositoryRef","refs/heads/main"),("issuer","other")]:
            x=self.fixture();x[0]["verificationResult"]["signature"]["certificate"][k]=v
            with self.assertRaises(ValueError):n._verified_receipt(x,self.p,self.now)
    def test_scope(self):
        for k,v in [("environment","PROD"),("gate","cost"),("promotion_authorized",True),("module_count",True)]:
            x=self.fixture();x[0]["verificationResult"]["statement"]["predicate"][k]=v
            with self.assertRaises(ValueError):n._verified_receipt(x,self.p,self.now)
    def test_time_and_duplicates(self):
        for x,t in [(self.fixture()*2,self.now),(self.fixture(),self.now+3600),(self.fixture(),self.now-3600)]:
            with self.assertRaises(ValueError):n._verified_receipt(x,self.p,t)
    def test_no_release(self):
        r=n._verified_receipt(self.fixture(),self.p,self.now)
        with patch.object(n,"verify_build",return_value=r),patch.object(n.time,"time",return_value=self.now):
            result=n.review_build("fixture",self.p)
        self.assertEqual(len(result["review"]["missing"]),11);self.assertFalse(result["review"]["deployment_authorized"])
    def test_wrong_archive(self):
        import tempfile
        with tempfile.NamedTemporaryFile() as f:
            f.write(b"not the artifact");f.flush()
            with self.assertRaisesRegex(ValueError,"ARTIFACT_DIGEST_DENIED"):n.verify_build(f.name,self.p)
