from dataclasses import dataclass

@dataclass(frozen=True)
class RecoveryEvidence:
    backup_ref: str
    rollback_ref: str
    rebuild_ref: str
    restore_tested: bool
    rollback_tested: bool
    rebuild_tested: bool

    def validate(self) -> None:
        if not all((self.backup_ref, self.rollback_ref, self.rebuild_ref)):
            raise ValueError("backup, rollback and rebuild evidence references are required")

    @property
    def green(self) -> bool:
        self.validate()
        return all((self.restore_tested, self.rollback_tested, self.rebuild_tested))
