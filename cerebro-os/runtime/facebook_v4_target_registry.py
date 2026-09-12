from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FacebookV4Target:
    scenario_id: int
    format_name: str
    runtime_format: str
    mutates_facebook: bool
    current_status: str
    finalizer_scenario_id: int | None = None


TARGETS = {
    9533715: FacebookV4Target(9533715, "Texto orgánico simple", "text", True, "OLD_INACTIVE_PRESERVED"),
    9533724: FacebookV4Target(9533724, "Texto + enlace", "link", True, "OLD_INACTIVE_PRESERVED"),
    9533532: FacebookV4Target(9533532, "Imagen", "image", True, "OLD_INACTIVE_PRESERVED"),
    9533564: FacebookV4Target(9533564, "Vídeo corto", "reel", True, "OLD_INACTIVE_PRESERVED", 9533584),
    9533967: FacebookV4Target(9533967, "Carrusel", "carousel", True, "OLD_INACTIVE_PRESERVED"),
    9533972: FacebookV4Target(9533972, "Vídeo largo", "video_long", True, "OLD_INACTIVE_PRESERVED", 9533974),
    9533976: FacebookV4Target(9533976, "Story", "story", False, "CORE_PREFLIGHT_INACTIVE_PRESERVED"),
}

MUTATING_TARGET_IDS = frozenset(k for k, v in TARGETS.items() if v.mutates_facebook)
NON_MUTATING_TARGET_IDS = frozenset(k for k, v in TARGETS.items() if not v.mutates_facebook)


def get_target(scenario_id: int) -> FacebookV4Target:
    try:
        return TARGETS[scenario_id]
    except KeyError as exc:
        raise ValueError("unknown Facebook V4 target scenario") from exc


def evaluate_target_cutover(*, scenario_id: int, caller_map_complete: bool,
                            replay_parity_green: bool, rollback_proven: bool,
                            runtime_live: bool, old_preserved: bool,
                            external_action_safety_green: bool) -> dict:
    target = get_target(scenario_id)
    gates = {
        "caller_map_complete": caller_map_complete,
        "replay_parity_green": replay_parity_green,
        "rollback_proven": rollback_proven,
        "runtime_live": runtime_live,
        "old_preserved": old_preserved,
        "external_action_safety_green": external_action_safety_green,
    }
    ready = all(gates.values())
    return {
        "scenario_id": scenario_id,
        "format_name": target.format_name,
        "runtime_format": target.runtime_format,
        "mutates_facebook": target.mutates_facebook,
        "finalizer_scenario_id": target.finalizer_scenario_id,
        "current_status": target.current_status,
        "gates": gates,
        "cutover_ready": ready,
        "deactivate_old_allowed": ready,
        "delete_old_allowed": False,
        "external_action_allowed": False,
        "requires_human": target.mutates_facebook and ready,
        "human_reason": "SIGNATURE_REQUIRED" if target.mutates_facebook and ready else None,
    }
