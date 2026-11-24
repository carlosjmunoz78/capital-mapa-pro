"""Additive CP189 promotion evidence gate. No deployment authority.
The trusted verifier is supplied by the runtime, never by a request.
A candidate is eligible for further review, not authorized to deploy.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Callable
from .promotion_gate import REQUIRED_GATES

@dataclass(frozen=True)
class Candidate:
    company_id: str
    engine_id: str
    environment: str
    version: str
    commit: str
    artifact_sha256: str

@dataclass(frozen=True)
class TrustedEvidence:
    gate: str
    candidate: Candidate
    evidence_id: str
    payload_sha256: str
    issuer: str
    observed_at: int
    expires_at: int
    result: str

def digest(payload: bytes) -> str:
    return sha256(payload).hexdigest()

def decide_verified(*, candidate: Candidate, gates: dict, evidence: dict,
                    trusted_lookup: Callable[[str, str], TrustedEvidence | None],
                    issuer_by_gate: dict[str, str], now: int,
                    policy_decision: str, human_required: bool) -> dict:
    """trusted_lookup must obtain an independently verified receipt, not parse caller claims."""
    def result(decision, reason, missing=()):
        return {"decision":decision,"reason":reason,"missing":tuple(missing),
                "deployment_authorized":False}
    if (type(candidate) is not Candidate or candidate.environment not in {"PREPROD","PROD"}
            or not all(isinstance(x,str) and x.strip() for x in
                       (candidate.company_id,candidate.engine_id,candidate.version))
            or not re.fullmatch(r"[0-9a-f]{40}",candidate.commit)
            or not re.fullmatch(r"[0-9a-f]{64}",candidate.artifact_sha256)
            or type(now) is not int or now<0 or type(human_required) is not bool):
        return result("BLOCKED","INVALID_CANDIDATE")
    if human_required:
        return result("HUMAN_REQUIRED","HUMAN_EXCEPTION")
    if policy_decision != "ALLOW":
        return result("BLOCKED" if policy_decision=="DENY" else "HUMAN_REQUIRED","POLICY_DENIED_OR_CONFLICT")
    if set(gates)!=set(REQUIRED_GATES) or set(evidence)!=set(REQUIRED_GATES):
        return result("BLOCKED","GATE_SET_MISMATCH")
    if set(issuer_by_gate)!=set(REQUIRED_GATES) or not all(isinstance(v,str) and v for v in issuer_by_gate.values()):
        return result("BLOCKED","TRUST_POLICY_INCOMPLETE")
    missing=[]; seen=set()
    for gate in REQUIRED_GATES:
        item=evidence[gate]
        if gates[gate] is not True or type(item) is not dict or set(item)!={"id","payload"}:
            missing.append(gate); continue
        eid,payload=item["id"],item["payload"]
        if (not isinstance(eid,str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{8,128}",eid)
                or eid in seen or type(payload) is not bytes or not (0<len(payload)<=1048576)):
            missing.append(gate); continue
        seen.add(eid)
        try:
            r=trusted_lookup(gate,eid)
            if (type(r) is not TrustedEvidence or r.gate!=gate or r.candidate!=candidate
                    or r.evidence_id!=eid or r.payload_sha256!=digest(payload)
                    or r.issuer!=issuer_by_gate[gate] or r.result!="PASS"
                    or type(r.observed_at) is not int or type(r.expires_at) is not int
                    or not (0<=r.observed_at<=now<r.expires_at)):
                missing.append(gate)
        except Exception:
            missing.append(gate)
    if missing:
        return result("BLOCKED","UNVERIFIED_EVIDENCE",missing)
    return result("PREPROD_REVIEW_CANDIDATE" if candidate.environment=="PREPROD" else "PROD_REVIEW_CANDIDATE",
                  "VERIFIED_EVIDENCE_REQUIRES_SEPARATE_RELEASE_AUTHORITY")
