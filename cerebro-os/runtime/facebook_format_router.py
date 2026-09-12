from dataclasses import dataclass

_ALLOWED_ENVIRONMENTS = {"LAB", "TEST", "PREPROD", "PROD", "Producción"}


@dataclass(frozen=True)
class FacebookFormatRouteRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    format: str


@dataclass(frozen=True)
class FacebookFormatRoute:
    target_scenario_id: int | None
    target_kind: str
    status: str
    external_action_allowed: bool
    requires_human: bool


# Contract observed in Make CORE router V4 (9533991).
# This table is routing metadata only. It does not authorize or perform publishing.
_V4_TARGETS = {
    "Texto orgánico simple": (9533715, "facebook_text"),
    "Texto + enlace": (9533724, "facebook_link"),
    "Imagen": (9533532, "facebook_image"),
    "Vídeo corto": (9533564, "facebook_video_short"),
    "Carrusel": (9533967, "facebook_carousel"),
    "Vídeo largo": (9533972, "facebook_video_long"),
    "Story": (9533976, "facebook_story"),
}

# Historical routers superseded by the V4 routing contract / target-specific runtimes.
HISTORICAL_ROUTER_IDS = frozenset({9528432, 9530604, 9531140, 9533487, 9533499})
CURRENT_ROUTER_ID = 9533991


def route_facebook_format(req: FacebookFormatRouteRequest) -> dict:
    required = (req.company_id, req.engine_id, req.environment, req.version, req.publication_id, req.run_id, req.format)
    if any(not str(value).strip() for value in required):
        raise ValueError("missing required Facebook format route input")
    if req.environment not in _ALLOWED_ENVIRONMENTS:
        raise ValueError("invalid environment")

    target = _V4_TARGETS.get(req.format)
    base = {
        "company_id": req.company_id,
        "engine_id": req.engine_id,
        "environment": req.environment,
        "version": req.version,
        "publication_id": req.publication_id,
        "run_id": req.run_id,
        "format": req.format,
        "router_scenario_id": CURRENT_ROUTER_ID,
        "platform_state": "FACEBOOK_NOT_CALLED",
        "external_action_allowed": False,
    }
    if target is None:
        return {
            **base,
            "target_scenario_id": None,
            "target_kind": "blocked",
            "status": "BLOCKED_UNKNOWN_FORMAT",
            "requires_human": True,
            "human_reason": "LOW_CONFIDENCE",
        }

    target_scenario_id, target_kind = target
    return {
        **base,
        "target_scenario_id": target_scenario_id,
        "target_kind": target_kind,
        "status": "ROUTED",
        "requires_human": False,
    }


def historical_router_can_retire(*, scenario_id: int, caller_map_complete: bool,
                                 replay_parity_green: bool, rollback_proven: bool,
                                 target_runtime_live: bool) -> bool:
    if scenario_id not in HISTORICAL_ROUTER_IDS:
        raise ValueError("scenario is not a registered historical Facebook router")
    return all((caller_map_complete, replay_parity_green, rollback_proven, target_runtime_live))
