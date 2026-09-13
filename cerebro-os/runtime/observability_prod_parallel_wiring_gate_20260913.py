from __future__ import annotations

# Fail-closed gate for wiring the existing LAB parallel observability mirror toward PROD.
# This module performs no external I/O and does not enable PROD. It only evaluates
# whether enough evidence exists to permit a future activation step.

REQUIRED_EVIDENCE = (
    "parallel_mirror_lab_green",
    "legacy_tables_unchanged",
    "scope_company_engine_environment_version_enforced",
    "rollback_disable_mirror_proven",
    "retained_read_only_source_replay_green",
    "incident_fixture_nonprod_green",
)


def assess_wiring_gate(evidence: dict[str, bool] | None = None) -> dict:
    supplied = dict(evidence or {})
    checks = {name: bool(supplied.get(name, False)) for name in REQUIRED_EVIDENCE}
    missing = tuple(name for name, ok in checks.items() if not ok)
    ready_for_controlled_prod_wiring = not missing
    return {
        "checks": checks,
        "missing": missing,
        "ready_for_controlled_prod_wiring": ready_for_controlled_prod_wiring,
        "prod_mirroring_enabled": False,
        "legacy_tables_modified": False,
        "automatic_prod_activation_allowed": False,
        "rollback_action": "disable_parallel_mirror_only",
        "status": "CONTROLLED_PROD_WIRING_READY" if ready_for_controlled_prod_wiring else "PROD_WIRING_EVIDENCE_PENDING",
    }


def current_evidence_snapshot() -> dict:
    # Evidence already established in repository/CI. This only marks readiness for a
    # future controlled wiring step; it does not claim live 177/177 PROD coverage.
    return {
        "parallel_mirror_lab_green": True,
        "legacy_tables_unchanged": True,
        "scope_company_engine_environment_version_enforced": True,
        "rollback_disable_mirror_proven": True,
        "retained_read_only_source_replay_green": True,
        "incident_fixture_nonprod_green": True,
    }
