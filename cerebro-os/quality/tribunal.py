from dataclasses import dataclass

REQUIRED_GATES = (
    "contracts",
    "permissions",
    "tests",
    "evaluation",
    "observability",
    "rollback",
    "backup",
    "rebuild",
    "cost",
    "policy",
    "tenant_isolation",
)
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class TribunalDecision:
    engine_id: str
    gates: dict[str, bool]
    company_id: str = "GLOBAL"
    environment: str = "LAB"
    evidence_refs: dict[str, str] | None = None
    version: str = "1.0.0"

    def missing(self) -> tuple[str, ...]:
        return tuple(gate for gate in REQUIRED_GATES if not self.gates.get(gate, False))

    def missing_evidence(self) -> tuple[str, ...]:
        refs = self.evidence_refs or {}
        return tuple(gate for gate in REQUIRED_GATES if self.gates.get(gate, False) and not str(refs.get(gate, "")).strip())

    @property
    def approved(self) -> bool:
        if not self.engine_id.strip() or not self.company_id.strip() or not self.version.strip():
            return False
        if self.environment not in VALID_ENVIRONMENTS:
            return False
        return not self.missing() and not self.missing_evidence()
