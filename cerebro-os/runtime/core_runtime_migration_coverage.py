from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MigrationCoverage:
    legacy_capability: str
    runtime_target: str
    scope: str
    parity_required: bool = True
    external_mutation_allowed: bool = False
    delete_old_allowed: bool = False


COVERAGE = (
    MigrationCoverage("router_master", "runtime/dispatcher.py", "deterministic routing"),
    MigrationCoverage("dispatcher_notion_redes", "runtime/dispatcher.py", "dispatch classification"),
    MigrationCoverage("logs_universales", "runtime/execution_log.py", "execution audit log"),
    MigrationCoverage("facebook_analytics_windows", "runtime/facebook_analytics_windows.py", "24h/7d window planning"),
    MigrationCoverage("facebook_caller_map", "runtime/caller_map.py", "legacy caller wrapping"),
    MigrationCoverage("core_inactive_classification", "runtime/core_inactive_migration_policy.py", "migration/quarantine policy"),
    MigrationCoverage("old_new_parity", "runtime/core_migration_replay.py", "replay parity gate"),
)


def coverage_report(*, company_id: str, environment: str, version: str, existing_targets: set[str]) -> dict:
    if not all((company_id, environment, version)):
        raise ValueError("company_id, environment and version required")
    if environment not in {"LAB", "PREPROD"}:
        raise ValueError("migration coverage verification is LAB/PREPROD only")

    rows = []
    for item in COVERAGE:
        exists = item.runtime_target in existing_targets
        rows.append({
            "legacy_capability": item.legacy_capability,
            "runtime_target": item.runtime_target,
            "target_exists": exists,
            "parity_required": item.parity_required,
            "external_mutation_allowed": item.external_mutation_allowed,
            "delete_old_allowed": item.delete_old_allowed,
        })

    missing = tuple(row["runtime_target"] for row in rows if not row["target_exists"])
    return {
        "company_id": company_id,
        "environment": environment,
        "version": version,
        "covered_capabilities": len(rows) - len(missing),
        "total_capabilities": len(rows),
        "missing_targets": missing,
        "all_targets_present": not missing,
        "old_preserved": True,
        "prod_cutover_allowed": False,
        "status": "GREEN_CODE_CI" if not missing else "MIGRATION_TARGETS_MISSING",
        "rows": tuple(rows),
    }
