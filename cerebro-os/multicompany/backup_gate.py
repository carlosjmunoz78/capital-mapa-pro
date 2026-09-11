from __future__ import annotations

CHECKS = (
    "backup_verified",
    "restore_verified",
    "rebuild_verified",
    "rollback_verified",
)


def backup_gate(
    *,
    company_id: str,
    backup_verified: bool,
    restore_verified: bool,
    rebuild_verified: bool,
    rollback_verified: bool,
    evidence_refs: dict[str, str] | None = None,
) -> dict:
    """Fail closed unless every recovery claim has a concrete evidence ref."""
    if not company_id or not company_id.strip():
        raise ValueError("company_id required")
    checks = {
        "backup_verified": bool(backup_verified),
        "restore_verified": bool(restore_verified),
        "rebuild_verified": bool(rebuild_verified),
        "rollback_verified": bool(rollback_verified),
    }
    missing = tuple(name for name, value in checks.items() if not value)
    refs = evidence_refs or {}
    missing_evidence = tuple(
        name for name, value in checks.items()
        if value and not str(refs.get(name, "")).strip()
    )
    return {
        "company_id": company_id,
        "ready": not missing and not missing_evidence,
        "missing": missing,
        "missing_evidence": missing_evidence,
    }
