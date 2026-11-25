"""Native CI evidence adapter for one explicitly pinned PREPROD rehearsal.
No signer, trust enrollment, or release authority. Existing CP189 remains unchanged.
The trusted runtime, not a request, supplies the artifact and GitHub CLI installation.
"""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import json
import re
import subprocess
import tempfile
import time
import zipfile
from .promotion_gate import REQUIRED_GATES
from .verified_promotion_gate import Candidate, TrustedEvidence, decide_verified

REPO="carlosjmunoz78/capital-mapa-pro"
WORKFLOW=REPO+"/.github/workflows/cerebro-core-preprod-build.yml"
PREDICATE="https://github.com/"+REPO+"/cerebro/ci-tests-evidence/v1"
ISSUER="github:1139292249:ci-tests:preprod"
ID="github-attestation:72096863"
COMMIT="b4d39f00a99cf583ab9ccff73c14ebb80ffdab55"
HEAD="2f22d1a95f18afaf37b37514b0d4736819e44e35"
ARTIFACT="f18ccfab3a3a3fbaf9aecc7d4934ccd2e1a53409e8a403e05dddcb37c4f35b80"
MANIFEST="b264fdef83cab0818a97d64361de50243c5b5118dab6270cdf757c9a91bc9f1e"
CANDIDATE=Candidate("fenix","FACT-001","PREPROD","1.1.0",COMMIT,ARTIFACT)
EXPECTED={"schema":"cerebro.ci.tests-evidence.v1","environment":"PREPROD",
    "gate":"tests","scope":"CORE_BUILD_REGRESSION_ONLY","result":"PASS",
    "source_commit":COMMIT,"pr_head":HEAD,"run_id":45596144769,
    "artifact_id":15012739243,"artifact_sha256":ARTIFACT,
    "manifest_sha256":MANIFEST,"module_count":26,
    "deployment_authorized":False,"promotion_authorized":False}

def _verify_output(data,now):
    # Only call on stdout from the actual trusted verifier; JSON alone is not proof.
    if type(now) is not int or type(data) is not list or len(data)>32:
        raise ValueError("VERIFIER_OUTPUT_DENIED")
    accepted=[]
    for item in data:
        v=item.get("verificationResult",{})
        cert=v.get("signature",{}).get("certificate",{})
        st=v.get("statement",{})
        uri="https://github.com/"+WORKFLOW+"@refs/pull/290/merge"
        required={"issuer":"https://token.actions.githubusercontent.com",
            "subjectAlternativeName":uri,"buildSignerURI":uri,
            "buildSignerDigest":COMMIT,"sourceRepositoryDigest":COMMIT,
            "sourceRepositoryIdentifier":"1139292249",
            "sourceRepositoryOwnerIdentifier":"130542695",
            "sourceRepositoryRef":"refs/pull/290/merge","runnerEnvironment":"github-hosted",
            "buildTrigger":"pull_request","runInvocationURI":"https://github.com/"+REPO+"/actions/runs/45596144769/attempts/1"}
        if any(cert.get(k)!=x for k,x in required.items()):
            continue
        if st.get("_type")!="https://in-toto.io/Statement/v1" or st.get("predicateType")!=PREDICATE:
            continue
        if st.get("subject")!=[{"name":"candidate.zip","digest":{"sha256":ARTIFACT}}]:
            continue
        if json.dumps(st.get("predicate"),sort_keys=True)!=json.dumps(EXPECTED,sort_keys=True):
            continue
        stamps=[t for t in v.get("verifiedTimestamps",[]) if t.get("type")=="Tlog" and t.get("uri")=="https://rekor.sigstore.dev"]
        if len(stamps)!=1:
            continue
        stamp=stamps[0].get("timestamp","")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",stamp):
            continue
        observed=int(datetime.fromisoformat(stamp.replace("Z","+00:00")).timestamp())
        if not 0<=observed<=now<observed+3600:
            continue
        accepted.append(observed)
    if len(accepted)!=1:
        raise ValueError("NO_UNIQUE_FRESH_PINNED_ATTESTATION")
    payload=json.dumps(EXPECTED,sort_keys=True,separators=(",",":")).encode()
    return payload,TrustedEvidence("tests",CANDIDATE,ID,sha256(payload).hexdigest(),ISSUER,accepted[0],accepted[0]+3600,"PASS")

def verify_native_tests(artifact_path):
    """Fresh verification via official gh CLI. Never accept uploaded verification JSON."""
    with Path(artifact_path).open("rb") as f:
        blob=f.read(2_000_001)
    if len(blob)>2_000_000 or sha256(blob).hexdigest()!=ARTIFACT:
        raise ValueError("ARTIFACT_DIGEST_DENIED")
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/"candidate.zip"
        path.write_bytes(blob)
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
            "--signer-workflow",WORKFLOW,"--source-digest",COMMIT,
            "--deny-self-hosted-runners","--predicate-type",PREDICATE,"--format","json"],
            capture_output=True,check=True,timeout=60)
        if len(proc.stdout)>2_000_000:
            raise ValueError("VERIFICATION_SIZE_DENIED")
        return _verify_output(json.loads(proc.stdout),int(time.time()))

def review_native_tests(artifact_path):
    """Partial review only. No issuer is enrolled for other gates here."""
    payload,receipt=verify_native_tests(artifact_path)
    now=int(time.time())
    result=decide_verified(candidate=CANDIDATE,
        gates={g:g=="tests" for g in REQUIRED_GATES},
        evidence={g:{"id":ID,"payload":payload} if g=="tests" else {} for g in REQUIRED_GATES},
        trusted_lookup=lambda g,e:receipt if (g,e)==("tests",ID) else None,
        issuer_by_gate={g:ISSUER if g=="tests" else "UNCONFIGURED:"+g for g in REQUIRED_GATES},
        now=now,policy_decision="ALLOW",human_required=False)
    if result["decision"]!="BLOCKED" or set(result["missing"])!=set(REQUIRED_GATES)-{"tests"} or result["deployment_authorized"] is not False:
        raise ValueError("PARTIAL_REVIEW_CONTRACT_DENIED")
    return {"status":"NATIVE_TESTS_GATE_VERIFIED","evidence_id":ID,"candidate":CANDIDATE.__dict__,
        "observed_at":receipt.observed_at,"expires_at":receipt.expires_at,"review":result}
