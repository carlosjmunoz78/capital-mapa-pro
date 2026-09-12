from __future__ import annotations

VALID_TARGETS = {"ISOLATED_RESTORE", "PREPROD_CLONE"}
REQUIRED_EVIDENCE = (
    "backup_identifier",
    "restore_target_identifier",
    "started_at",
    "completed_at",
    "integrity_check_ref",
    "application_smoke_ref",
    "cleanup_or_retention_ref",
)


def assess_provider_restore_drill(evidence: dict) -> dict:
    target = str(evidence.get("target_type", "")).strip()
    checks = {name: bool(str(evidence.get(name, "")).strip()) for name in REQUIRED_EVIDENCE}
    missing = tuple(name for name, ok in checks.items() if not ok)
    isolated = target in VALID_TARGETS
    prod_target = target == "PROD"
    restore_green = isolated and not missing and not prod_target
    return {
        "target_type": target,
        "isolated_target_required": True,
        "isolated_target_valid": isolated,
        "checks": checks,
        "missing": missing,
        "restore_green": restore_green,
        "provider_restore_ref_eligible": restore_green,
        "destructive_prod_restore_allowed": False,
        "prod_mutation_allowed": False,
        "human_reason": "HIGH_RISK" if prod_target else None,
        "status": "PROVIDER_RESTORE_DRILL_GREEN" if restore_green else "PROVIDER_RESTORE_DRILL_EVIDENCE_PENDING",
    }
