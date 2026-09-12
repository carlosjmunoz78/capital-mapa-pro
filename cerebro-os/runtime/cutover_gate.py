from dataclasses import dataclass
from enum import Enum


class CutoverDecision(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class CutoverEvidence:
    scenario_id: int
    replacement_runtime: str
    caller_map_complete: bool
    replay_parity_green: bool
    rollback_proven: bool
    target_runtime_live: bool
    old_preserved: bool
    external_action_safe: bool


@dataclass(frozen=True)
class CutoverAssessment:
    decision: CutoverDecision
    blockers: tuple[str, ...]


def assess_cutover(evidence: CutoverEvidence) -> CutoverAssessment:
    blockers: list[str] = []
    if not evidence.replacement_runtime:
        blockers.append("replacement_runtime_missing")
    if not evidence.caller_map_complete:
        blockers.append("caller_map_incomplete")
    if not evidence.replay_parity_green:
        blockers.append("replay_parity_not_green")
    if not evidence.rollback_proven:
        blockers.append("rollback_not_proven")
    if not evidence.target_runtime_live:
        blockers.append("target_runtime_not_live")
    if not evidence.old_preserved:
        blockers.append("old_not_preserved")
    if not evidence.external_action_safe:
        blockers.append("external_action_safety_not_proven")
    return CutoverAssessment(
        decision=CutoverDecision.BLOCKED if blockers else CutoverDecision.READY,
        blockers=tuple(blockers),
    )


def rollback_required(*, new_health_green: bool, parity_green: bool, unexpected_external_action: bool) -> bool:
    return (not new_health_green) or (not parity_green) or unexpected_external_action
