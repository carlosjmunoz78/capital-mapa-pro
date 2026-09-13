from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryExternalEvidence:
    source: str
    evidence_type: str
    proves_source_backup: bool
    proves_rebuild: bool
    proves_rollback_rehearsal: bool
    proves_provider_restore: bool
    destructive_action_allowed: bool = False


LIVE_EVIDENCE = {
    "make_9527263": RecoveryExternalEvidence(
        source="Make scenario 9527263 PREVENTIVO DLQ y recuperación segura V1",
        evidence_type="safe_read_retry_simulation",
        proves_source_backup=False,
        proves_rebuild=False,
        proves_rollback_rehearsal=False,
        proves_provider_restore=False,
    ),
    "make_9524813": RecoveryExternalEvidence(
        source="Make scenario 9524813 PREVENTIVO Facebook compuerta central V1",
        evidence_type="test_only_pre_execution_gate",
        proves_source_backup=False,
        proves_rebuild=False,
        proves_rollback_rehearsal=False,
        proves_provider_restore=False,
    ),
    "github_pinned_source_snapshot": RecoveryExternalEvidence(
        source="Git commit e0e5b41e3a05198d015af7bcd0387d4ff3c66e48",
        evidence_type="immutable_git_source_snapshot",
        proves_source_backup=True,
        proves_rebuild=False,
        proves_rollback_rehearsal=False,
        proves_provider_restore=False,
    ),
    "github_ci_runtime_rehearsal": RecoveryExternalEvidence(
        source="GitHub Actions runtime boot and rollback rehearsal",
        evidence_type="runtime_ci_rehearsal",
        proves_source_backup=False,
        proves_rebuild=True,
        proves_rollback_rehearsal=True,
        proves_provider_restore=False,
    ),
}


def summarize_recovery_external_evidence() -> dict:
    items = tuple(LIVE_EVIDENCE.values())
    checks = {
        "source_backup": any(x.proves_source_backup for x in items),
        "rebuild": any(x.proves_rebuild for x in items),
        "rollback_rehearsal": any(x.proves_rollback_rehearsal for x in items),
        "provider_restore": any(x.proves_provider_restore for x in items),
    }
    return {
        "checks": checks,
        "source_recovery_partial": checks["rebuild"] and checks["rollback_rehearsal"],
        "source_recovery_green": checks["source_backup"] and checks["rebuild"] and checks["rollback_rehearsal"],
        "provider_restore_green": checks["provider_restore"],
        "recovery_green": all(checks.values()),
        "destructive_action_allowed": False,
        "status": "EXTERNAL_PROOF_PENDING" if not all(checks.values()) else "RECOVERY_GREEN",
        "missing": tuple(name for name, ok in checks.items() if not ok),
    }
