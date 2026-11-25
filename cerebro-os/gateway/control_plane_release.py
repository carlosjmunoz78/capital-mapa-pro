"""Parallel production admission boundary. No execution, signer or deployment authority.

Keep the legacy control plane unchanged until callers and release authority are
independently verified. This candidate is deliberately fail-closed for PROD.
"""
from governance.verified_promotion_gate import Candidate, decide_verified
from gateway.control_plane import control_decision

def review_control(*, candidate, route_status, policy_decision, supervisor_state,
                   tribunal_approved, promotion_decision, evidence_refs,
                   gates, evidence, trusted_lookup, issuer_by_gate, now,
                   human_required=False):
    def denied(reason, **detail):
        return {"status":"BLOCKED","reason":reason,"deployment_authorized":False,**detail}
    if type(candidate) is not Candidate or candidate.environment not in {"PREPROD","PROD"}:
        return denied("CANDIDATE_SCOPE_DENIED")
    # Route, policy, supervisor and tribunal remain mandatory. A legacy string
    # result is not a cryptographic release authorization.
    legacy=control_decision(route_status=route_status,policy_decision=policy_decision,
        supervisor_state=supervisor_state,tribunal_approved=tribunal_approved,
        promotion_decision=promotion_decision,environment=candidate.environment,
        evidence_refs=evidence_refs)
    if legacy["status"]!="ALLOW_EXECUTION":
        return {**legacy,"deployment_authorized":False}
    review=decide_verified(candidate=candidate,gates=gates,evidence=evidence,
        trusted_lookup=trusted_lookup,issuer_by_gate=issuer_by_gate,now=now,
        policy_decision=policy_decision,human_required=human_required)
    return _finish_review(review)


def _finish_review(review):
    if review["decision"]=="HUMAN_REQUIRED":
        return {"status":"HUMAN_REQUIRED","reason":review["reason"],"deployment_authorized":False}
    if review["decision"] not in {"PREPROD_REVIEW_CANDIDATE","PROD_REVIEW_CANDIDATE"}:
        return {"status":"BLOCKED","reason":"VERIFIED_GATES_REQUIRED","review":review,"deployment_authorized":False}
    return {"status":"BLOCKED","reason":"SEPARATE_RELEASE_AUTHORITY_REQUIRED","review":review,"deployment_authorized":False}


def review_stored_control(*, candidate, route_status, policy_decision, supervisor_state,
                          tribunal_approved, promotion_decision, evidence_refs,
                          receipt_ids, store_path, trust, clock, human_required=False):
    """Acceptance composition only. Runtime must supply trusted context and keys.

    Uses the existing consistent, read-only SQLite snapshot verifier. Neither
    this entry point nor a successful review grants release authority.
    Do not expose directly as a caller-controlled endpoint.
    """
    if type(candidate) is not Candidate or candidate.environment not in {"PREPROD","PROD"}:
        return {"status":"BLOCKED","reason":"CANDIDATE_SCOPE_DENIED","deployment_authorized":False}
    legacy=control_decision(route_status=route_status,policy_decision=policy_decision,
        supervisor_state=supervisor_state,tribunal_approved=tribunal_approved,
        promotion_decision=promotion_decision,environment=candidate.environment,
        evidence_refs=evidence_refs)
    if legacy["status"]!="ALLOW_EXECUTION":
        return {**legacy,"deployment_authorized":False}
    from governance.promotion_receipt_store import review_stored_candidate
    review=review_stored_candidate(candidate=candidate,receipt_ids=receipt_ids,
        store_path=store_path,trust=trust,clock=clock,policy_decision=policy_decision,
        human_required=human_required)
    return _finish_review(review)
