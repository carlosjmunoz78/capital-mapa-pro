"""Recurring native CI evidence for the certified PREPROD runtime only.
Trusted CI context supplies immutable build coordinates, not request data.
This adapter verifies bytes and provider signatures; never authorizes release.
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import json
import re
import subprocess
import tempfile
import time
import zipfile
from .native_ci_tests import REPO, WORKFLOW, PREDICATE, ISSUER, MANIFEST
from .promotion_gate import REQUIRED_GATES
from .verified_promotion_gate import Candidate, TrustedEvidence, decide_verified

@dataclass(frozen=True)
class BuildPolicy:
    commit: str
    head: str
    run_id: int
    attempt: int
    artifact_id: int
    artifact_sha256: str

    def __post_init__(self):
        if any(type(x) is not str or not re.fullmatch(r"[0-9a-f]{40}",x) for x in (self.commit,self.head)):
            raise ValueError("BUILD_COMMIT_DENIED")
        if type(self.artifact_sha256) is not str or not re.fullmatch(r"[0-9a-f]{64}",self.artifact_sha256):
            raise ValueError("BUILD_DIGEST_DENIED")
        if any(type(x) is not int or not 0<x<2**63 for x in (self.run_id,self.attempt,self.artifact_id)):
            raise ValueError("BUILD_ID_DENIED")
    @property
    def candidate(self):
        return Candidate("fenix","FACT-001","PREPROD","1.1.0",self.commit,self.artifact_sha256)
    @property
    def evidence_id(self):
        return f"github-ci:{self.run_id}:{self.attempt}:{self.artifact_id}"
    @property
    def predicate(self):
        return {"schema":"cerebro.ci.tests-evidence.v1","environment":"PREPROD",
          "gate":"tests","scope":"CORE_BUILD_REGRESSION_ONLY","result":"PASS",
          "source_commit":self.commit,"pr_head":self.head,"run_id":self.run_id,
          "artifact_id":self.artifact_id,"artifact_sha256":self.artifact_sha256,
          "manifest_sha256":MANIFEST,"module_count":26,
          "deployment_authorized":False,"promotion_authorized":False}

def _canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)

def _verified_receipt(data,policy,now):
    if type(policy) is not BuildPolicy or type(now) is not int or type(data) is not list or not 0<len(data)<=32:
        raise ValueError("VERIFIER_OUTPUT_DENIED")
    uri="https://github.com/"+WORKFLOW+"@refs/pull/290/merge"
    required={"issuer":"https://token.actions.githubusercontent.com",
        "subjectAlternativeName":uri,"buildSignerURI":uri,
        "buildSignerDigest":policy.commit,"sourceRepositoryDigest":policy.commit,
        "sourceRepositoryIdentifier":"1139292249","sourceRepositoryOwnerIdentifier":"130542695",
        "sourceRepositoryRef":"refs/pull/290/merge","runnerEnvironment":"github-hosted",
        "buildTrigger":"pull_request","runInvocationURI":f"https://github.com/{REPO}/actions/runs/{policy.run_id}/attempts/{policy.attempt}"}
    accepted=[]
    for item in data:
        v=item.get("verificationResult",{})
        cert=v.get("signature",{}).get("certificate",{})
        st=v.get("statement",{})
        if any(cert.get(k)!=x for k,x in required.items()):
            continue
        if st.get("_type")!="https://in-toto.io/Statement/v1" or st.get("predicateType")!=PREDICATE:
            continue
        if st.get("subject")!=[{"name":"candidate.zip","digest":{"sha256":policy.artifact_sha256}}]:
            continue
        if _canonical(st.get("predicate"))!=_canonical(policy.predicate):
            continue
        stamps=[t for t in v.get("verifiedTimestamps",[]) if t.get("type")=="Tlog" and t.get("uri")=="https://rekor.sigstore.dev"]
        if len(stamps)!=1:
            continue
        stamp=stamps[0].get("timestamp","")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",stamp):
            continue
        observed=int(datetime.fromisoformat(stamp.replace("Z","+00:00")).timestamp())
        if 0<=observed<=now<observed+3600:
            accepted.append(observed)
    if len(accepted)!=1:
        raise ValueError("NO_UNIQUE_FRESH_ATTESTATION")
    payload=_canonical(policy.predicate).encode()
    return payload,TrustedEvidence("tests",policy.candidate,policy.evidence_id,sha256(payload).hexdigest(),ISSUER,accepted[0],accepted[0]+3600,"PASS")

def verify_build(artifact_path,policy):
    if type(policy) is not BuildPolicy:
        raise ValueError("TRUSTED_POLICY_REQUIRED")
    with Path(artifact_path).open("rb") as f:
        blob=f.read(2_000_001)
    if len(blob)>2_000_000 or sha256(blob).hexdigest()!=policy.artifact_sha256:
        raise ValueError("ARTIFACT_DIGEST_DENIED")
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/"candidate.zip";path.write_bytes(blob)
        with zipfile.ZipFile(path) as z:
            names=z.namelist()
            if len(names)!=27 or len(set(names))!=27 or sum(i.file_size for i in z.infolist())>2_000_000:
                raise ValueError("ARCHIVE_SCOPE_DENIED")
            m=json.loads(z.read("manifest.json"))
            if sha256(json.dumps(m,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()!=MANIFEST:
                raise ValueError("MANIFEST_DENIED")
            if (m.get("company_id"),m.get("environment"),m.get("version"),m.get("promotion_allowed"))!=("fenix","PREPROD","1.1.0",False):
                raise ValueError("SCOPE_DENIED")
            files=m["files"]
            if len(files)!=26 or set(names)!=set(files)|{"manifest.json"}:
                raise ValueError("FILE_SET_DENIED")
            for name,digest in files.items():
                if not re.fullmatch(r"[\w.-]+\.mjs",name) or sha256(z.read(name)).hexdigest()!=digest:
                    raise ValueError("MODULE_DRIFT")
        proc=subprocess.run(["gh","attestation","verify",str(path),"-R",REPO,
            "--signer-workflow",WORKFLOW,"--source-digest",policy.commit,
            "--deny-self-hosted-runners","--predicate-type",PREDICATE,"--format","json"],
            capture_output=True,check=True,timeout=60)
        if len(proc.stdout)>2_000_000:
            raise ValueError("VERIFICATION_SIZE_DENIED")
        return _verified_receipt(json.loads(proc.stdout),policy,int(time.time()))

def review_build(artifact_path,policy):
    payload,receipt=verify_build(artifact_path,policy)
    now=int(time.time())
    result=decide_verified(candidate=policy.candidate,
        gates={g:g=="tests" for g in REQUIRED_GATES},
        evidence={g:{"id":policy.evidence_id,"payload":payload} if g=="tests" else {} for g in REQUIRED_GATES},
        trusted_lookup=lambda g,e:receipt if (g,e)==("tests",policy.evidence_id) else None,
        issuer_by_gate={g:ISSUER if g=="tests" else "UNCONFIGURED:"+g for g in REQUIRED_GATES},
        now=now,policy_decision="ALLOW",human_required=False)
    if result["decision"]!="BLOCKED" or set(result["missing"])!=set(REQUIRED_GATES)-{"tests"} or result["deployment_authorized"] is not False:
        raise ValueError("PARTIAL_REVIEW_DENIED")
    return {"status":"RECURRING_NATIVE_TESTS_GATE_VERIFIED","evidence_id":policy.evidence_id,
        "candidate":asdict(policy.candidate),"observed_at":receipt.observed_at,
        "expires_at":receipt.expires_at,"review":result}
