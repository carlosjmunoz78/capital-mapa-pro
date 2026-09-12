from dataclasses import dataclass


INSTAGRAM_PROD_TARGETS = {
    9534139: "image",
    9534084: "carousel",
    9534087: "reel",
}


@dataclass(frozen=True)
class InstagramCutoverEvidence:
    scenario_id: int
    caller_map_complete: bool
    replay_parity_green: bool
    rollback_proven: bool
    target_runtime_live: bool
    old_preserved: bool
    external_action_safe: bool


def assess_instagram_cutover(e: InstagramCutoverEvidence) -> dict:
    if e.scenario_id not in INSTAGRAM_PROD_TARGETS:
        raise ValueError("unknown Instagram PROD target")
    blockers = []
    gates = {
        "CALLER_MAP_INCOMPLETE": e.caller_map_complete,
        "REPLAY_PARITY_NOT_GREEN": e.replay_parity_green,
        "ROLLBACK_NOT_PROVEN": e.rollback_proven,
        "TARGET_RUNTIME_NOT_LIVE": e.target_runtime_live,
        "OLD_NOT_PRESERVED": e.old_preserved,
        "EXTERNAL_ACTION_NOT_SAFE": e.external_action_safe,
    }
    for blocker, ok in gates.items():
        if not ok:
            blockers.append(blocker)
    return {
        "scenario_id": e.scenario_id,
        "format": INSTAGRAM_PROD_TARGETS[e.scenario_id],
        "cutover_ready": not blockers,
        "deactivate_old_allowed": not blockers,
        "delete_old_allowed": False,
        "external_action_allowed": False,
        "requires_human": not blockers,
        "human_reason": "SIGNATURE_REQUIRED" if not blockers else None,
        "blockers": tuple(blockers),
    }


def inventory() -> dict[int, str]:
    return dict(INSTAGRAM_PROD_TARGETS)
