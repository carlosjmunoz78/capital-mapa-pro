from dataclasses import dataclass


@dataclass(frozen=True)
class FacebookPreflightContract:
    scenario_id: int
    format_key: str
    runtime: str
    status: str
    old_preserved: bool = True
    external_action_allowed: bool = False
    autoactivate_old_allowed: bool = False
    delete_old_allowed: bool = False
    prod_cutover_allowed: bool = False


LIVE_PREFLIGHT_MAP = {
    9531078: FacebookPreflightContract(
        9531078, "link", "facebook_link_preflight.py", "LIVE_CONTRACT_CAPTURED"
    ),
    9531133: FacebookPreflightContract(
        9531133, "image", "facebook_image_preflight.py", "LIVE_CONTRACT_CAPTURED"
    ),
    9533424: FacebookPreflightContract(
        9533424, "video_short", "facebook_video_short_preflight.py", "LIVE_CONTRACT_CAPTURED"
    ),
    9533987: FacebookPreflightContract(
        9533987, "carousel", "carousel_preflight.py", "LIVE_CONTRACT_CAPTURED"
    ),
    9533988: FacebookPreflightContract(
        9533988, "video_long", "video_long_preflight.py", "LIVE_CONTRACT_CAPTURED"
    ),
    9533976: FacebookPreflightContract(
        9533976, "story", "story_preflight.py", "LIVE_CONTRACT_CAPTURED"
    ),
}


EXPECTED_INVARIANTS = {
    9531078: {
        "platform_state": "FACEBOOK_NOT_CALLED",
        "environment": "TEST",
        "requires_human": False,
        "evidence": ("publication", "production_order", "calendar", "programming", "url"),
    },
    9531133: {
        "platform_state": "FACEBOOK_NOT_CALLED",
        "environment": "TEST",
        "requires_human": False,
        "evidence": ("publication", "production_order", "calendar", "asset", "programming", "http_head"),
    },
    9533424: {
        "platform_state": "FACEBOOK_NOT_CALLED",
        "environment": "TEST",
        "requires_human": True,
        "evidence": ("publication", "production_order", "calendar", "programming", "asset", "http_head"),
    },
    9533987: {
        "platform_state": "FACEBOOK_NOT_CALLED",
        "photo_min": 2,
        "photo_max": 30,
        "real_publish_authorized": False,
    },
    9533988: {
        "platform_state": "FACEBOOK_NOT_CALLED",
        "http_min": 200,
        "http_max": 399,
        "duration_seconds_min_exclusive": 90,
        "real_publish_authorized": False,
    },
    9533976: {
        "provider_state": "NATIVE_CONNECTOR_UNAVAILABLE",
        "queue_status": "BLOCKED_PROVIDER_NOT_CONNECTED",
        "requires_human": True,
        "automatic_action": "Mantener en cola sin publicar",
    },
}


def get_live_contract(scenario_id: int) -> dict:
    try:
        contract = LIVE_PREFLIGHT_MAP[scenario_id]
        invariants = EXPECTED_INVARIANTS[scenario_id]
    except KeyError as exc:
        raise ValueError("unknown Facebook preflight scenario") from exc
    return {
        "scenario_id": contract.scenario_id,
        "format_key": contract.format_key,
        "runtime": contract.runtime,
        "status": contract.status,
        "invariants": invariants,
        "old_preserved": contract.old_preserved,
        "external_action_allowed": contract.external_action_allowed,
        "autoactivate_old_allowed": contract.autoactivate_old_allowed,
        "delete_old_allowed": contract.delete_old_allowed,
        "prod_cutover_allowed": contract.prod_cutover_allowed,
    }


def all_fail_closed() -> bool:
    return all(
        item.old_preserved
        and not item.external_action_allowed
        and not item.autoactivate_old_allowed
        and not item.delete_old_allowed
        and not item.prod_cutover_allowed
        for item in LIVE_PREFLIGHT_MAP.values()
    )
