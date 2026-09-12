from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class RecoveryEvidence:
    company_id: str
    environment: str
    version: str
    source_backup_ref: str = ""
    rebuild_ref: str = ""
    rollback_rehearsal_ref: str = ""
    provider_restore_ref: str = ""


def assess_recovery_readiness(evidence: RecoveryEvidence) -> dict:
    """Evidence-first recovery gate. Never infers provider restore from source rebuild proof."""
    if not evidence.company_id.strip() or not evidence.version.strip():
        raise ValueError("company_id and version required")
    if evidence.environment not in VALID_ENVIRONMENTS:
        raise ValueError("invalid environment")

    checks = {
        "source_backup": bool(evidence.source_backup_ref.strip()),
        "rebuild": bool(evidence.rebuild_ref.strip()),
        "rollback_rehearsal": bool(evidence.rollback_rehearsal_ref.strip()),
        "provider_restore": bool(evidence.provider_restore_ref.strip()),
    }
    missing = tuple(name for name, ok in checks.items() if not ok)

    source_recovery_green = checks["source_backup"] and checks["rebuild"] and checks["rollback_rehearsal"]
    provider_restore_green = checks["provider_restore"]
    recovery_green = source_recovery_green and provider_restore_green

    return {
        "company_id": evidence.company_id,
        "environment": evidence.environment,
        "version": evidence.version,
        "checks": checks,
        "missing": missing,
        "source_recovery_green": source_recovery_green,
        "provider_restore_green": provider_restore_green,
        "recovery_green": recovery_green,
        "prod_candidate_allowed": recovery_green,
        "destructive_restore_allowed": False,
        "human_reason": "HIGH_RISK" if evidence.environment == "PROD" and not recovery_green else None,
    }
