from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class RecoveryPlan:
    backup_defined: bool
    backup_verified: bool
    rollback_defined: bool
    rollback_verified: bool
    rebuild_defined: bool
    rebuild_verified: bool

    def promotion_ready(self) -> bool:
        return all([
            self.backup_defined,
            self.backup_verified,
            self.rollback_defined,
            self.rollback_verified,
            self.rebuild_defined,
            self.rebuild_verified,
        ])
