from __future__ import annotations


def backup_gate(*, company_id: str, backup_verified: bool, restore_verified: bool, rebuild_verified: bool, rollback_verified: bool) -> dict:
    if not company_id:
        raise ValueError("company_id required")
    checks = {
        "backup_verified": bool(backup_verified),
        "restore_verified": bool(restore_verified),
        "rebuild_verified": bool(rebuild_verified),
        "rollback_verified": bool(rollback_verified),
    }
    missing = tuple(name for name, value in checks.items() if not value)
    return {
        "company_id": company_id,
        "ready": not missing,
        "missing": missing,
    }
