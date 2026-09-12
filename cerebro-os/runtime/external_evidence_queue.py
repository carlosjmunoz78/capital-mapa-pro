from __future__ import annotations

from dataclasses import dataclass

PRIORITY = {
    "SECURITY_INCIDENT": 0,
    "HIGH_RISK": 1,
    "LEGAL_REQUIRED": 2,
    "SIGNATURE_REQUIRED": 3,
    "MONEY_LIMIT": 4,
    "POLICY_CONFLICT": 5,
    "LOW_CONFIDENCE": 6,
    "CUSTOMER_HUMAN_REQUEST": 7,
    "EXTERNAL_PROOF": 20,
}


@dataclass(frozen=True)
class EvidenceGap:
    company_id: str
    engine_id: str
    environment: str
    version: str
    gap_id: str
    reason: str
    evidence_needed: str
    blocks_prod_candidate: bool = True


def normalize_gap(gap: EvidenceGap) -> dict:
    if not all((gap.company_id.strip(), gap.engine_id.strip(), gap.version.strip(), gap.gap_id.strip())):
        raise ValueError("scope and gap_id required")
    if gap.environment not in {"LAB", "PREPROD", "PROD"}:
        raise ValueError("invalid environment")
    if gap.reason not in PRIORITY:
        raise ValueError("unknown evidence-gap reason")
    if not gap.evidence_needed.strip():
        raise ValueError("evidence_needed required")
    return {
        "company_id": gap.company_id,
        "engine_id": gap.engine_id,
        "environment": gap.environment,
        "version": gap.version,
        "gap_id": gap.gap_id,
        "reason": gap.reason,
        "evidence_needed": gap.evidence_needed,
        "blocks_prod_candidate": gap.blocks_prod_candidate,
        "priority": PRIORITY[gap.reason],
    }


def build_queue(gaps: tuple[EvidenceGap, ...]) -> tuple[dict, ...]:
    normalized = [normalize_gap(gap) for gap in gaps]
    normalized.sort(key=lambda item: (item["priority"], item["company_id"], item["engine_id"], item["gap_id"]))
    return tuple(normalized)
