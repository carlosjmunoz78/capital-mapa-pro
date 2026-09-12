from dataclasses import dataclass


@dataclass(frozen=True)
class LegacySupersession:
    legacy_scenario_id: int
    replacement_scenario_id: int
    replacement_runtime: str
    status: str
    reason: str
    old_external_action_allowed: bool = False
    replacement_external_action_allowed: bool = False


SUPERSESSION_MAP = {
    9530582: LegacySupersession(
        legacy_scenario_id=9530582,
        replacement_scenario_id=9531078,
        replacement_runtime="facebook_link_preflight.py",
        status="RETIRE_CANDIDATE_AFTER_CALLER_MAP",
        reason=(
            "V1 audits Facebook TEST link candidates, OP and calendar but only counts "
            "programming relations. V2 additionally reads the programming record directly "
            "and is therefore a strict functional superset for the safe preflight path."
        ),
    ),
    9528450: LegacySupersession(
        legacy_scenario_id=9528450,
        replacement_scenario_id=9530484,
        replacement_runtime="facebook_text_direct_preflight.py",
        status="RETIRE_CANDIDATE_AFTER_CALLER_MAP",
        reason=(
            "V1 audits pending Facebook text plus OP governance. V2 reads publication, OP, "
            "calendar and programming directly without rollups and preserves the same "
            "no-publish safety invariant, making it the preferred replacement contract."
        ),
    ),
    9532848: LegacySupersession(
        legacy_scenario_id=9532848,
        replacement_scenario_id=9533424,
        replacement_runtime="facebook_video_short_preflight.py",
        status="RETIRE_CANDIDATE_AFTER_CALLER_MAP",
        reason=(
            "Historical V1 was explicitly blocked by missing calendar access and must not be "
            "reused as V2. V2 captures the complete direct evidence set and remains fail-closed."
        ),
    ),
}


def get_supersession(scenario_id: int) -> LegacySupersession:
    try:
        return SUPERSESSION_MAP[scenario_id]
    except KeyError as exc:
        raise ValueError("scenario is not registered as superseded") from exc


def can_retire_legacy(*, scenario_id: int, caller_map_complete: bool, replay_parity_green: bool,
                      rollback_proven: bool, target_runtime_live: bool) -> bool:
    get_supersession(scenario_id)
    return all((caller_map_complete, replay_parity_green, rollback_proven, target_runtime_live))
