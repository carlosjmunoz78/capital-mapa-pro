from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class RecoveryEvidence:
    backup_ref: str
    rollback_ref: str
    rebuild_ref: str
    restore_tested: bool
    rollback_tested: bool
    rebuild_tested: bool
    company_id: str = ""
    engine_id: str = ""
    environment: str = ""
    version: str = ""

    def validate(self) -> None:
        if not all((
            self.backup_ref.strip(), self.rollback_ref.strip(), self.rebuild_ref.strip(),
            self.company_id.strip(), self.engine_id.strip(), self.version.strip(),
        )):
            raise ValueError("backup, rollback, rebuild and canonical scope references are required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")

    @property
    def green(self) -> bool:
        self.validate()
        return all((self.restore_tested, self.rollback_tested, self.rebuild_tested))
