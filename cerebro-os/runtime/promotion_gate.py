from __future__ import annotations

from dataclasses import dataclass

CANONICAL_HUMAN_REASONS = {
    "LEGAL_REQUIRED",
    "SIGNATURE_REQUIRED",
    "LOW_CONFIDENCE",
    "HIGH_RISK",
    "POLICY_CONFLICT",
    "SECURITY_INCIDENT",
    "MONEY_LIMIT",
    "CUSTOMER_HUMAN_REQUEST",
}


@dataclass(frozen=True)
class PromotionEvidence:
    company_id: str
    engine_id: str
    environment: str
    version: str
    contracts: bool
    permissions: bool
    tests: bool
    evaluation: bool
    tribunal: bool
    observability: bool
    rollback: bool
    backup: bool
    rebuild: bool
    cost_measured: bool
    policy: bool
    environment_evidence: bool
    human_reason: str | None = None


def assess_promotion(evidence: PromotionEvidence) -> dict:
    if not all((evidence.company_id.strip(), evidence.engine_id.strip(), evidence.version.strip())):
        raise ValueError("company_id, engine_id and version required")
    if evidence.environment not in {"LAB", "PREPROD", "PROD"}:
        raise ValueError("invalid environment")
    if evidence.human_reason is not None and evidence.human_reason not in CANONICAL_HUMAN_REASONS:
        raise ValueError("non-canonical human reason")

    checks = {
        "contracts": evidence.contracts,
        "permissions": evidence.permissions,
        "tests": evidence.tests,
        "evaluation": evidence.evaluation,
        "tribunal": evidence.tribunal,
        "observability": evidence.observability,
        "rollback": evidence.rollback,
        "backup": evidence.backup,
        "rebuild": evidence.rebuild,
        "cost_measured": evidence.cost_measured,
        "policy": evidence.policy,
        "environment_evidence": evidence.environment_evidence,
    }
    missing = tuple(name for name, ok in checks.items() if not ok)
    technical_green = not missing
    human_blocked = evidence.human_reason is not None
    prod_candidate = technical_green and not human_blocked

    return {
        "company_id": evidence.company_id,
        "engine_id": evidence.engine_id,
        "environment": evidence.environment,
        "version": evidence.version,
        "missing": missing,
        "technical_green": technical_green,
        "human_blocked": human_blocked,
        "human_reason": evidence.human_reason,
        "prod_candidate": prod_candidate,
        "prod_green": False,
        "gradual_promotion_required": True,
        "automatic_external_action_allowed": False,
    }
