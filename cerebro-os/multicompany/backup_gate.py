from __future__ import annotations

CHECKS = (
    "backup_verified",
    "restore_verified",
    "rebuild_verified",
    "rollback_verified",
)
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


def backup_gate(
    *,
    company_id: str,
    backup_verified: bool,
    restore_verified: bool,
    rebuild_verified: bool,
    rollback_verified: bool,
    evidence_refs: dict[str, str] | None = None,
    environment: str = "LAB",
    version: str = "1.0.0",
) -> dict:
    """Fail closed unless every recovery claim has exact-scope concrete evidence."""
    if not company_id or not company_id.strip() or not version.strip():
        raise ValueError("company_id and version required")
    if environment not in VALID_ENVIRONMENTS:
        raise ValueError("invalid environment")
    checks = {
        "backup_verified": bool(backup_verified),
        "restore_verified": bool(restore_verified),
        "rebuild_verified": bool(rebuild_verified),
        "rollback_verified": bool(rollback_verified),
    }
    missing = tuple(name for name, value in checks.items() if not value)
    refs = evidence_refs or {}
    missing_evidence = tuple(name for name, value in checks.items() if value and not str(refs.get(name, "")).strip())
    scope_match = (
        refs.get("company_id") == company_id
        and refs.get("environment") == environment
        and refs.get("version") == version
    )
    return {
        "company_id": company_id,
        "environment": environment,
        "version": version,
        "ready": not missing and not missing_evidence and scope_match,
        "missing": missing,
        "missing_evidence": missing_evidence,
        "scope_match": scope_match,
    }
