from __future__ import annotations

from dataclasses import dataclass

CANONICAL_HUMAN_REASONS = {
    "LEGAL_REQUIRED", "SIGNATURE_REQUIRED", "LOW_CONFIDENCE", "HIGH_RISK",
    "POLICY_CONFLICT", "SECURITY_INCIDENT", "MONEY_LIMIT", "CUSTOMER_HUMAN_REQUEST",
}
VALID_STATUSES = {"PENDING", "GREEN", "RED", "BLOCKED", "HUMAN_REQUIRED"}
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class EngineResult:
    company_id: str
    loop_id: str
    engine_id: str
    environment: str
    status: str
    evidence_ref: str | None = None
    human_reason: str | None = None

    def validate(self, sequence: tuple[str, ...], lab_only: set[str], target_environment: str) -> None:
        if not self.company_id.strip():
            raise ValueError("company_id required")
        if self.engine_id not in sequence:
            raise ValueError("engine_id not in loop")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.environment != target_environment:
            raise ValueError("cross-environment result denied")
        if self.status not in VALID_STATUSES:
            raise ValueError("invalid status")
        if self.status == "GREEN" and not (self.evidence_ref and self.evidence_ref.strip()):
            raise ValueError("GREEN requires evidence_ref")
        if self.status == "HUMAN_REQUIRED" and self.human_reason not in CANONICAL_HUMAN_REASONS:
            raise ValueError("invalid HUMAN_REQUIRED reason")
        if self.engine_id in lab_only and self.environment != "LAB":
            raise ValueError("LAB engine cannot be promoted outside LAB")


class PlatformLoopController:
    def __init__(self, company_id: str, loops: dict[str, tuple[str, ...]], lab_only: set[str] | frozenset[str], *, environment: str = "LAB") -> None:
        if not company_id.strip():
            raise ValueError("company_id required")
        if not loops:
            raise ValueError("loops required")
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        self.company_id = company_id
        self.environment = environment
        self.loops = dict(loops)
        self.loop_order = tuple(loops)
        self.lab_only = set(lab_only)
        if environment != "LAB":
            incompatible = tuple(sorted(engine_id for sequence in self.loops.values() for engine_id in sequence if engine_id in self.lab_only))
            if incompatible:
                raise ValueError(f"LAB-only engines present in {environment} controller: {incompatible}")
        self._state: dict[str, dict[str, EngineResult]] = {
            loop_id: {
                engine_id: EngineResult(company_id, loop_id, engine_id, environment, "PENDING")
                for engine_id in sequence
            }
            for loop_id, sequence in self.loops.items()
        }

    def next_loop(self) -> str | None:
        for loop_id in self.loop_order:
            if self.loop_status(loop_id) != "GREEN":
                return loop_id
        return None

    def next_engine(self, loop_id: str) -> str | None:
        sequence = self.loops[loop_id]
        for engine_id in sequence:
            if self._state[loop_id][engine_id].status != "GREEN":
                return engine_id
        return None

    def can_advance(self, loop_id: str, engine_id: str) -> bool:
        sequence = self.loops[loop_id]
        idx = sequence.index(engine_id)
        return all(
            self._state[loop_id][e].status == "GREEN"
            and bool(self._state[loop_id][e].evidence_ref and self._state[loop_id][e].evidence_ref.strip())
            for e in sequence[:idx]
        )

    def update(self, result: EngineResult) -> None:
        if result.loop_id not in self.loops:
            raise ValueError("unknown loop")
        result.validate(self.loops[result.loop_id], self.lab_only, self.environment)
        if result.company_id != self.company_id:
            raise ValueError("cross-company update denied")
        if result.status == "GREEN" and not self.can_advance(result.loop_id, result.engine_id):
            raise ValueError("dependencies not GREEN with evidence")
        self._state[result.loop_id][result.engine_id] = result

    def loop_status(self, loop_id: str) -> str:
        results = tuple(self._state[loop_id].values())
        states = tuple(r.status for r in results)
        if all(r.status == "GREEN" and r.evidence_ref and r.evidence_ref.strip() and r.environment == self.environment for r in results):
            return "GREEN"
        if "BLOCKED" in states:
            return "BLOCKED"
        if "HUMAN_REQUIRED" in states:
            return "HUMAN_REQUIRED"
        if "RED" in states:
            return "RED"
        return "IN_PROGRESS"

    def system_status(self) -> str:
        statuses = tuple(self.loop_status(loop_id) for loop_id in self.loop_order)
        if all(s == "GREEN" for s in statuses):
            return "GREEN"
        if "BLOCKED" in statuses:
            return "BLOCKED"
        if "HUMAN_REQUIRED" in statuses:
            return "HUMAN_REQUIRED"
        if "RED" in statuses:
            return "RED"
        return "IN_PROGRESS"

    def snapshot(self) -> dict:
        return {
            "company_id": self.company_id,
            "environment": self.environment,
            "loops": {loop_id: dict(items) for loop_id, items in self._state.items()},
        }
