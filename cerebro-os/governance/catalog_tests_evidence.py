"""CP189 acceptance of actual catalog package tests, not integrity-only evidence."""
import json,hashlib,subprocess,time,re
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
from .verified_promotion_gate import Candidate,TrustedEvidence,decide_verified
from .promotion_gate import REQUIRED_GATES
REPO="carlosjmunoz78/capital-mapa-pro"
WF=REPO+"/.github/workflows/cerebro-catalog-tests-evidence.yml"
TYPE="https://github.com/"+REPO+"/cerebro/catalog-tests/v1"
SHA="3037a23330f0049ed7457d11103212c2b338c5fcb03b4b77cfef25aec4711fd4"
SOURCE="70a6fa8608c52b7b832e6c46704b0663bf4c2c7f"
CANDIDATE=Candidate("fenix","FACT-001","PREPROD","1.2.0",SOURCE,SHA)
ISSUER="github:1139292249:catalog-tests:preprod"
def predicate(commit,run,attempt):
    return {"schema":"cerebro.catalog.tests.v1","candidate":asdict(CANDIDATE),"gate":"tests",
        "scope":"OFFLINE_CATALOG_ACCEPTANCE","result":"PASS","tests_run":16,"failures":0,"errors":0,
        "workflow_commit":commit,"run_id":run,"attempt":attempt,
        "deployment_authorized":False,"runtime_identity_verified":False}
def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def verify_output(data,commit,run,attempt,now):
    if not re.fullmatch(r"[0-9a-f]{40}",commit) or type(run) is not int or run<=0 or type(attempt) is not int or attempt<=0:raise ValueError("CONTEXT")
    expected=predicate(commit,run,attempt)
    uri="https://github.com/"+WF+"@refs/pull/290/merge"
    required={"issuer":"https://token.actions.githubusercontent.com","subjectAlternativeName":uri,"buildSignerURI":uri,
        "buildSignerDigest":commit,"sourceRepositoryDigest":commit,"sourceRepositoryIdentifier":"1139292249",
        "sourceRepositoryOwnerIdentifier":"130542695","sourceRepositoryRef":"refs/pull/290/merge",
        "runnerEnvironment":"github-hosted","buildTrigger":"pull_request",
        "runInvocationURI":f"https://github.com/{REPO}/actions/runs/{run}/attempts/{attempt}"}
    accepted=[]
    for item in data:
        v=item.get("verificationResult",{});c=v.get("signature",{}).get("certificate",{});s=v.get("statement",{})
        if any(c.get(k)!=x for k,x in required.items()):continue
        if s.get("_type")!="https://in-toto.io/Statement/v1" or s.get("predicateType")!=TYPE or s.get("subject")!=[{"name":"catalog.zip","digest":{"sha256":SHA}}] or canonical(s.get("predicate"))!=canonical(expected):continue
        stamps=[x for x in v.get("verifiedTimestamps",[]) if x.get("type")=="Tlog" and x.get("uri")=="https://rekor.sigstore.dev"]
        if len(stamps)!=1:continue
        stamp=stamps[0]["timestamp"]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",stamp):continue
        t=int(datetime.fromisoformat(stamp.replace("Z","+00:00")).timestamp())
        if 0<=t<=now<t+3600:accepted.append(t)
    if len(accepted)!=1:raise ValueError("ATTESTATION_NOT_UNIQUE_OR_FRESH")
    payload=canonical(expected);eid=f"github-catalog-tests:{run}:{attempt}"
    receipt=TrustedEvidence("tests",CANDIDATE,eid,hashlib.sha256(payload).hexdigest(),ISSUER,accepted[0],accepted[0]+3600,"PASS")
    result=decide_verified(candidate=CANDIDATE,gates={g:g=="tests" for g in REQUIRED_GATES},
        evidence={g:{"id":eid,"payload":payload} if g=="tests" else {} for g in REQUIRED_GATES},
        trusted_lookup=lambda g,e:receipt if (g,e)==("tests",eid) else None,
        issuer_by_gate={g:ISSUER if g=="tests" else "UNCONFIGURED:"+g for g in REQUIRED_GATES},
        now=now,policy_decision="ALLOW",human_required=False)
    if result["decision"]!="BLOCKED" or set(result["missing"])!=set(REQUIRED_GATES)-{"tests"} or result["deployment_authorized"] is not False:raise ValueError("GATE_CONTRACT")
    return {"status":"CATALOG_TESTS_ADMITTED","candidate":asdict(CANDIDATE),"evidence_id":eid,"expires_at":receipt.expires_at,"review":result}
def verify(path,commit,run,attempt):
    p=Path(path)
    if p.stat().st_size!=11728 or hashlib.sha256(p.read_bytes()).hexdigest()!=SHA:raise ValueError("ARTIFACT_DRIFT")
    output=subprocess.check_output(["gh","attestation","verify",str(p),"-R",REPO,"--signer-workflow",WF,"--source-digest",commit,"--deny-self-hosted-runners","--predicate-type",TYPE,"--format","json"],timeout=60)
    return verify_output(json.loads(output),commit,run,attempt,int(time.time()))
