from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class V4TargetEvidence:
    scenario_id: int
    trigger_kind: str
    status: str
    mutates_facebook: bool
    finalizer_scenario_id: int | None = None


LIVE_V4_TARGETS = {
    9533715: V4TargetEvidence(9533715, "scheduled", "inactive", True, None),
    9533724: V4TargetEvidence(9533724, "scheduled", "inactive", True, None),
    9533532: V4TargetEvidence(9533532, "scheduled", "inactive", True, None),
    9533564: V4TargetEvidence(9533564, "scheduled", "inactive", True, 9533584),
    9533967: V4TargetEvidence(9533967, "on-demand", "inactive", True, None),
    9533972: V4TargetEvidence(9533972, "on-demand", "inactive", True, 9533974),
    9533976: V4TargetEvidence(9533976, "on-demand", "inactive", False, None),
}


def evaluate_v4_target_cutover(*, scenario_id: int, caller_map_complete: bool,
                               replay_parity_green: bool, rollback_proven: bool,
                               runtime_live: bool, old_preserved: bool,
                               external_action_safe: bool) -> dict:
    evidence = LIVE_V4_TARGETS.get(scenario_id)
    if evidence is None:
        raise ValueError("unknown Facebook V4 target")

    gates = {
        "caller_map_complete": caller_map_complete,
        "replay_parity_green": replay_parity_green,
        "rollback_proven": rollback_proven,
        "runtime_live": runtime_live,
        "old_preserved": old_preserved,
        "external_action_safe": external_action_safe,
    }
    ready = all(gates.values())
    return {
        "scenario_id": scenario_id,
        "trigger_kind": evidence.trigger_kind,
        "old_status": evidence.status,
        "mutates_facebook": evidence.mutates_facebook,
        "finalizer_scenario_id": evidence.finalizer_scenario_id,
        "gates": gates,
        "cutover_ready": ready,
        "deactivate_old_allowed": ready,
        "delete_old_allowed": False,
        "external_action_allowed": False,
        "requires_human": evidence.mutates_facebook and ready,
        "human_reason": "SIGNATURE_REQUIRED" if evidence.mutates_facebook and ready else None,
    }


def safety_replay_fixture(*, scenario_id: int, platform_state: str,
                          idempotency_state: str, analytics_windows_ready: bool,
                          retry_publish_allowed: bool) -> dict:
    if scenario_id not in LIVE_V4_TARGETS:
        raise ValueError("unknown Facebook V4 target")
    if retry_publish_allowed:
        return {"parity_green": False, "reason": "RETRY_PUBLISH_MUST_REMAIN_BLOCKED"}
    if platform_state not in {"PUBLISHED", "UPLOAD_ACCEPTED", "FACEBOOK_NOT_CALLED"}:
        return {"parity_green": False, "reason": "UNSUPPORTED_PLATFORM_STATE"}
    if platform_state == "UPLOAD_ACCEPTED" and idempotency_state == "COMMITTED":
        return {"parity_green": False, "reason": "PROCESSING_CANNOT_COMMIT_IDEMPOTENCY"}
    if analytics_windows_ready and idempotency_state != "COMMITTED":
        return {"parity_green": False, "reason": "ANALYTICS_BEFORE_COMMIT"}
    return {
        "parity_green": True,
        "reason": None,
        "external_action_allowed": False,
        "delete_old_allowed": False,
    }
