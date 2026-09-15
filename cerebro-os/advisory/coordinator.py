from __future__ import annotations

from .models import AdvisoryDecision, DomainOpinion

STATUS_PRIORITY = {
    "GREEN": 0,
    "AMBER": 1,
    "HUMAN_REQUIRED": 2,
    "BLOCKED": 3,
    "RED": 4,
}


def coordinate(case_id: str, routed_domains: tuple[str, ...], opinions: tuple[DomainOpinion, ...], audit_refs: tuple[str, ...] = ()) -> AdvisoryDecision:
    if not routed_domains:
        raise ValueError("routed domains required")
    opinion_map = {op.domain: op for op in opinions}
    if len(opinion_map) != len(opinions):
        raise ValueError("duplicate domain opinion")
    missing = [domain for domain in routed_domains if domain not in opinion_map]
    extra = [domain for domain in opinion_map if domain not in routed_domains]
    if missing:
        raise ValueError(f"missing domain opinions: {missing}")
    if extra:
        raise ValueError(f"unexpected domain opinions: {extra}")
    for op in opinions:
        op.validate()
        if op.status == "GREEN" and not op.source_refs:
            raise ValueError(f"GREEN opinion requires source refs: {op.domain}")

    overall = max((op.status for op in opinions), key=lambda x: STATUS_PRIORITY[x])
    decision = AdvisoryDecision(
        case_id=case_id,
        domains=routed_domains,
        opinions=opinions,
        overall_status=overall,
        audit_refs=audit_refs,
    )
    decision.validate()
    return decision
