from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SocialLegacyMapping:
    scenario_id: int
    network: str
    role: str
    runtime_targets: tuple[str, ...]
    old_status: str = "inactive"
    old_preserved: bool = True
    auto_activate_old: bool = False
    delete_old_allowed: bool = False
    external_action_allowed: bool = False
    prod_cutover_allowed: bool = False
    parity_required: bool = True


MAPPINGS: tuple[SocialLegacyMapping, ...] = (
    SocialLegacyMapping(
        scenario_id=9533991,
        network="Facebook",
        role="router_universal_formatos_v4",
        runtime_targets=(
            "runtime/facebook_format_router.py",
            "runtime/facebook_text_direct_preflight.py",
            "runtime/facebook_link_preflight.py",
            "runtime/facebook_image_preflight.py",
            "runtime/facebook_video_short_preflight.py",
            "runtime/carousel_preflight.py",
            "runtime/video_long_preflight.py",
            "runtime/story_preflight.py",
        ),
    ),
    SocialLegacyMapping(
        scenario_id=9534074,
        network="Instagram",
        role="router_universal_formatos_v1",
        runtime_targets=("runtime/instagram_prod_pipeline.py", "runtime/instagram_caller_parity.py"),
    ),
    SocialLegacyMapping(
        scenario_id=9534077,
        network="Instagram",
        role="preflight_imagen_v1",
        runtime_targets=("runtime/instagram_prod_pipeline.py", "runtime/instagram_caller_parity.py"),
    ),
    SocialLegacyMapping(
        scenario_id=9522560,
        network="LinkedIn",
        role="router_preflight_universal_v1",
        runtime_targets=("runtime/linkedin_preflight.py", "runtime/linkedin_caller_parity.py"),
    ),
    SocialLegacyMapping(
        scenario_id=9537662,
        network="YouTube",
        role="router_preflight_universal_v1",
        runtime_targets=("runtime/youtube_preflight.py", "runtime/youtube_caller_parity.py"),
    ),
)


def assess_social_inactive_mapping(scenario_id: int) -> dict:
    mapping = next((item for item in MAPPINGS if item.scenario_id == scenario_id), None)
    if mapping is None:
        return {
            "status": "MAPPING_MISSING",
            "green": False,
            "old_preserved": True,
            "external_action_allowed": False,
            "prod_cutover_allowed": False,
        }
    return {
        "status": "MAPPED_RUNTIME_TARGET",
        "green": True,
        "network": mapping.network,
        "role": mapping.role,
        "runtime_targets": mapping.runtime_targets,
        "old_status": mapping.old_status,
        "old_preserved": mapping.old_preserved,
        "auto_activate_old": mapping.auto_activate_old,
        "delete_old_allowed": mapping.delete_old_allowed,
        "external_action_allowed": mapping.external_action_allowed,
        "prod_cutover_allowed": mapping.prod_cutover_allowed,
        "parity_required": mapping.parity_required,
    }
