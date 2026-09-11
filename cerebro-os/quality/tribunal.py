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
)

@dataclass(frozen=True)
class TribunalDecision:
    engine_id: str
    gates: dict[str, bool]

    def missing(self) -> tuple[str, ...]:
        return tuple(gate for gate in REQUIRED_GATES if not self.gates.get(gate, False))

    @property
    def approved(self) -> bool:
        if not self.engine_id:
            return False
        return not self.missing()
