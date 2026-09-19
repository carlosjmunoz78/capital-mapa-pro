from __future__ import annotations

import json
from pathlib import Path

from observability.improvement_audit_store import ImprovementAuditStore


def company_improvement_status(root: Path, *, company_id: str, environment: str, version: str) -> dict:
    base = Path(root) / company_id / environment / version
    audit_path = base / "audit.db"
    checkpoint_path = base / "checkpoint.db"
    return {
        "company_id": company_id,
        "environment": environment,
        "version": version,
        "audit_present": audit_path.exists(),
        "checkpoint_present": checkpoint_path.exists(),
        "status": "READY" if audit_path.exists() or checkpoint_path.exists() else "NO_RUNTIME_STATE",
    }


def export_console_status(root: Path, configs: tuple[dict, ...]) -> dict:
    items = tuple(company_improvement_status(
        root,
        company_id=str(c["company_id"]),
        environment=str(c.get("environment","LAB")),
        version=str(c.get("version","1.0.0")),
    ) for c in configs)
    return {"service": "continuous-improvement", "companies": items, "count": len(items)}
