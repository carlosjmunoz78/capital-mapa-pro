from dataclasses import dataclass


LINKEDIN_PROD_TARGETS = {
    5554207: "text",
    9528327: "link",
    9522428: "image",
    9410589: "video",
}


@dataclass(frozen=True)
class LinkedInCutoverEvidence:
    scenario_id: int
    caller_map_complete: bool
    replay_parity_green: bool
    rollback_proven: bool
    target_runtime_live: bool
    old_preserved: bool
    external_action_safe: bool


def assess_linkedin_cutover(e: LinkedInCutoverEvidence) -> dict:
    if e.scenario_id not in LINKEDIN_PROD_TARGETS:
        raise ValueError("unknown LinkedIn PROD target")

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
        "format": LINKEDIN_PROD_TARGETS[e.scenario_id],
        "cutover_ready": not blockers,
        "deactivate_old_allowed": not blockers,
        "delete_old_allowed": False,
        "external_action_allowed": False,
        "requires_human": not blockers,
        "human_reason": "SIGNATURE_REQUIRED" if not blockers else None,
        "blockers": blockers,
    }


def inventory() -> dict[int, str]:
    return dict(LINKEDIN_PROD_TARGETS)
