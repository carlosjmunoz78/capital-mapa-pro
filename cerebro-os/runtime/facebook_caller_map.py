from dataclasses import dataclass


@dataclass(frozen=True)
class FacebookRouteTarget:
    format_name: str
    target_scenario_id: int
    target_runtime: str
    external_action_allowed: bool = False


# Evidence captured from Make CORE router 9533499 (V3).
# The router records these logical destinations but does not execute Facebook itself.
FACEBOOK_V3_TARGETS = {
    "Texto orgánico simple": FacebookRouteTarget(
        "Texto orgánico simple", 9530484, "facebook_text_direct_preflight.py"
    ),
    "Texto + enlace": FacebookRouteTarget(
        "Texto + enlace", 9531078, "facebook_link_preflight.py"
    ),
    "Imagen": FacebookRouteTarget(
        "Imagen", 9531133, "facebook_image_preflight.py"
    ),
    "Vídeo corto": FacebookRouteTarget(
        "Vídeo corto", 9533424, "facebook_video_short_preflight.py"
    ),
}

LEGACY_SUPERSEDED_IDS = frozenset({9530582, 9528450, 9532848})


def router_references_superseded_legacy() -> bool:
    return bool({t.target_scenario_id for t in FACEBOOK_V3_TARGETS.values()} & LEGACY_SUPERSEDED_IDS)


def get_target(format_name: str) -> FacebookRouteTarget:
    try:
        return FACEBOOK_V3_TARGETS[format_name]
    except KeyError as exc:
        raise ValueError("unsupported Facebook format") from exc
