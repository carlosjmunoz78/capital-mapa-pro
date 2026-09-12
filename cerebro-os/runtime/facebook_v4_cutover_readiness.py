from dataclasses import dataclass


V4_COMPONENTS = {
    9533715: "text",
    9533724: "link",
    9533532: "image",
    9533564: "reel",
    9533967: "carousel",
    9533972: "video_long",
    9533976: "story",
    9533584: "reel_finalizer",
    9533974: "video_long_finalizer",
}

MUTATORS = frozenset({9533715, 9533724, 9533532, 9533564, 9533967, 9533972})


@dataclass(frozen=True)
class ComponentEvidence:
    scenario_id: int
    caller_map_green: bool
    input_contract_green: bool
    replay_parity_green: bool
    rollback_ci_green: bool
    runtime_code_ci_green: bool
    target_runtime_live: bool
    old_preserved: bool
    external_action_safety_green: bool


def assess_component_cutover(e: ComponentEvidence) -> dict:
    if e.scenario_id not in V4_COMPONENTS:
        raise ValueError("unknown Facebook V4 component")

    checks = {
        "caller_map_green": e.caller_map_green,
        "input_contract_green": e.input_contract_green,
        "replay_parity_green": e.replay_parity_green,
        "rollback_ci_green": e.rollback_ci_green,
        "runtime_code_ci_green": e.runtime_code_ci_green,
        "target_runtime_live": e.target_runtime_live,
        "old_preserved": e.old_preserved,
        "external_action_safety_green": e.external_action_safety_green,
    }
    blockers = tuple(name for name, ok in checks.items() if not ok)
    lab_ci_ready = all(value for key, value in checks.items() if key != "target_runtime_live")
    cutover_ready = not blockers
    mutator = e.scenario_id in MUTATORS

    if cutover_ready:
        status = "CUTOVER_READY_HUMAN_GATE" if mutator else "CUTOVER_READY"
    elif lab_ci_ready and not e.target_runtime_live:
        status = "LAB_CI_READY_RUNTIME_LIVE_PENDING"
    else:
        status = "NOT_CUTOVER_READY"

    return {
        "scenario_id": e.scenario_id,
        "component": V4_COMPONENTS[e.scenario_id],
        "status": status,
        "lab_ci_ready": lab_ci_ready,
        "cutover_ready": cutover_ready,
        "blockers": blockers,
        "deactivate_old_allowed": cutover_ready and not mutator,
        "delete_old_allowed": False,
        "external_action_allowed": False,
        "requires_human": mutator and cutover_ready,
        "human_reason": "SIGNATURE_REQUIRED" if (mutator and cutover_ready) else None,
    }


def summarize_v4_readiness(items: list[ComponentEvidence]) -> dict:
    if {item.scenario_id for item in items} != set(V4_COMPONENTS):
        raise ValueError("V4 readiness summary requires the complete component set")
    assessed = [assess_component_cutover(item) for item in items]
    return {
        "total": len(assessed),
        "lab_ci_ready": sum(1 for row in assessed if row["lab_ci_ready"]),
        "cutover_ready": sum(1 for row in assessed if row["cutover_ready"]),
        "runtime_live_pending": sum(1 for row in assessed if row["status"] == "LAB_CI_READY_RUNTIME_LIVE_PENDING"),
        "prod_mutators": len(MUTATORS),
        "external_action_allowed": False,
        "delete_old_allowed": False,
        "components": assessed,
    }
