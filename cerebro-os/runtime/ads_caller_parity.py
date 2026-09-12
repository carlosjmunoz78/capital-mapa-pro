from dataclasses import dataclass

ADS_CORE_SCENARIO_ID = 9535463

@dataclass(frozen=True)
class AdsCutoverEvidence:
    scenario_id: int
    caller_map_complete: bool
    replay_parity_green: bool
    rollback_proven: bool
    target_runtime_live: bool
    old_preserved: bool
    money_gate_safe: bool


def assess_ads_cutover(e: AdsCutoverEvidence) -> dict:
    if e.scenario_id != ADS_CORE_SCENARIO_ID:
        raise ValueError("unknown ADS core target")
    gates = {
        "CALLER_MAP_INCOMPLETE": e.caller_map_complete,
        "REPLAY_PARITY_NOT_GREEN": e.replay_parity_green,
        "ROLLBACK_NOT_PROVEN": e.rollback_proven,
        "TARGET_RUNTIME_NOT_LIVE": e.target_runtime_live,
        "OLD_NOT_PRESERVED": e.old_preserved,
        "MONEY_GATE_NOT_SAFE": e.money_gate_safe,
    }
    blockers = tuple(name for name, ok in gates.items() if not ok)
    return {
        "scenario_id": e.scenario_id,
        "cutover_ready": not blockers,
        "deactivate_old_allowed": not blockers,
        "delete_old_allowed": False,
        "external_action_allowed": False,
        "requires_human": not blockers,
        "human_reason": "MONEY_LIMIT" if not blockers else None,
        "blockers": blockers,
    }
