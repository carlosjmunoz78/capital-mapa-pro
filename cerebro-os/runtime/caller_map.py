from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CallerEvidence:
    caller_id: str
    caller_kind: str
    target_scenario_id: int
    target_runtime: str | None
    environment: str
    active: bool
    evidence_ref: str


@dataclass(frozen=True)
class CallerMapResult:
    scenario_id: int
    callers: tuple[CallerEvidence, ...]
    complete: bool
    blockers: tuple[str, ...]


def build_caller_map(*, scenario_id: int, expected_runtime: str, evidence: Iterable[CallerEvidence]) -> CallerMapResult:
    rows = tuple(row for row in evidence if row.target_scenario_id == scenario_id)
    blockers: list[str] = []
    if not rows:
        blockers.append("NO_CALLER_EVIDENCE")
    for row in rows:
        if not row.caller_id.strip() or not row.evidence_ref.strip():
            blockers.append("INCOMPLETE_CALLER_EVIDENCE")
        if row.environment not in {"LAB", "TEST", "PREPROD", "PROD"}:
            blockers.append("INVALID_CALLER_ENVIRONMENT")
        if row.target_runtime and row.target_runtime != expected_runtime:
            blockers.append("RUNTIME_TARGET_MISMATCH")
    return CallerMapResult(
        scenario_id=scenario_id,
        callers=rows,
        complete=not blockers,
        blockers=tuple(sorted(set(blockers))),
    )


def can_cut_over_caller(*, caller_map_complete: bool, replay_parity_green: bool,
                        rollback_proven: bool, external_action_safe: bool) -> bool:
    return all((caller_map_complete, replay_parity_green, rollback_proven, external_action_safe))
