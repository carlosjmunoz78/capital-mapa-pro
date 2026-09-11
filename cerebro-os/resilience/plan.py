from __future__ import annotations

from dataclasses import dataclass

REQUIRED_RECOVERY_EVIDENCE = ("backup", "restore", "rollback", "rebuild")


@dataclass(frozen=True)
class RecoveryPlan:
    backup_defined: bool
    backup_verified: bool
    rollback_defined: bool
    rollback_verified: bool
    rebuild_defined: bool
    rebuild_verified: bool
    evidence_refs: dict[str, str] | None = None

    def missing_evidence(self) -> tuple[str, ...]:
        refs = self.evidence_refs or {}
        return tuple(key for key in REQUIRED_RECOVERY_EVIDENCE if not str(refs.get(key, "")).strip())

    def promotion_ready(self) -> bool:
        checks = (
            self.backup_defined,
            self.backup_verified,
            self.rollback_defined,
            self.rollback_verified,
            self.rebuild_defined,
            self.rebuild_verified,
        )
        return all(checks) and not self.missing_evidence()
