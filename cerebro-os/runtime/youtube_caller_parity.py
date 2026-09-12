from dataclasses import dataclass


YOUTUBE_PROD_TARGETS = {
    9537699: "short_private",
    9537702: "long_private",
}


@dataclass(frozen=True)
class YouTubeCutoverEvidence:
    scenario_id: int
    caller_map_complete: bool
    replay_parity_green: bool
    rollback_proven: bool
    target_runtime_live: bool
    old_preserved: bool
    external_action_safe: bool


def assess_youtube_cutover(e: YouTubeCutoverEvidence) -> dict:
    if e.scenario_id not in YOUTUBE_PROD_TARGETS:
        raise ValueError("unknown YouTube PROD target")

    gates = {
        "CALLER_MAP_INCOMPLETE": e.caller_map_complete,
        "REPLAY_PARITY_NOT_GREEN": e.replay_parity_green,
        "ROLLBACK_NOT_PROVEN": e.rollback_proven,
        "TARGET_RUNTIME_NOT_LIVE": e.target_runtime_live,
        "OLD_NOT_PRESERVED": e.old_preserved,
        "EXTERNAL_ACTION_NOT_SAFE": e.external_action_safe,
    }
    blockers = tuple(name for name, ok in gates.items() if not ok)

    return {
        "scenario_id": e.scenario_id,
        "format": YOUTUBE_PROD_TARGETS[e.scenario_id],
        "cutover_ready": not blockers,
        "deactivate_old_allowed": not blockers,
        "delete_old_allowed": False,
        "external_action_allowed": False,
        "requires_human": not blockers,
        "human_reason": "SIGNATURE_REQUIRED" if not blockers else None,
        "blockers": blockers,
    }


def inventory() -> dict[int, str]:
    return dict(YOUTUBE_PROD_TARGETS)
