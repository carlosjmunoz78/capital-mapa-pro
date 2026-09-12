from __future__ import annotations


FACTORY_LEGACY_MAP = {
    9533982: {
        "name": "Solicitud multimedia universal",
        "replacement_runtime": "media_request.py",
        "legacy_status": "inactive",
        "migration": "MIGRATE_TO_ENGINE_FACTORY_RUNTIME",
        "inputs": ("run_id", "production_order_id", "network", "environment", "format", "image_count", "needs_voice", "needs_presenter", "needs_video", "needs_editing", "priority"),
        "old_statuses": ("QUEUED_PROVIDERS_NOT_CONNECTED", "BLOCKED_BY_COST"),
        "old_external_action_allowed": False,
    },
    9534003: {
        "name": "Adaptador edición y subtítulos",
        "replacement_runtime": "provider_adapters.py:plan_editing",
        "legacy_status": "inactive",
        "migration": "MIGRATE_TO_ENGINE_FACTORY_RUNTIME",
        "inputs": ("run_id", "production_order_id", "environment", "video_asset_id", "subtitles", "music_profile", "template_profile"),
        "old_statuses": ("BLOCKED_PROVIDER_NOT_CONNECTED",),
        "difference": "VIDEO_EDITOR_API_NOT_CONNECTED",
        "old_external_action_allowed": False,
    },
    9534002: {
        "name": "Adaptador generación de vídeo",
        "replacement_runtime": "provider_adapters.py:plan_video_generation",
        "legacy_status": "inactive",
        "migration": "MIGRATE_TO_ENGINE_FACTORY_RUNTIME",
        "inputs": ("run_id", "production_order_id", "environment", "video_class", "target_duration_seconds", "aspect_ratio", "script_asset_id"),
        "old_statuses": ("BLOCKED_PROVIDER_NOT_CONNECTED",),
        "difference": "VIDEO_GENERATOR_API_NOT_CONNECTED",
        "old_external_action_allowed": False,
    },
    9533999: {
        "name": "Adaptador presentador y avatar",
        "replacement_runtime": "provider_adapters.py:plan_presenter",
        "legacy_status": "inactive",
        "migration": "MIGRATE_TO_ENGINE_FACTORY_RUNTIME",
        "inputs": ("run_id", "production_order_id", "environment", "presenter_profile", "audio_asset_id", "background_profile"),
        "old_statuses": ("BLOCKED_PROVIDER_NOT_CONNECTED",),
        "difference": "PRESENTER_API_NOT_CONNECTED",
        "old_external_action_allowed": False,
    },
    9533998: {
        "name": "Adaptador voz TTS",
        "replacement_runtime": "provider_adapters.py:plan_tts",
        "legacy_status": "inactive",
        "migration": "MIGRATE_TO_ENGINE_FACTORY_RUNTIME",
        "inputs": ("run_id", "production_order_id", "environment", "script", "language", "voice_profile"),
        "old_statuses": ("BLOCKED_PROVIDER_NOT_CONNECTED",),
        "difference": "TTS_API_NOT_CONNECTED",
        "old_external_action_allowed": False,
    },
    9533997: {
        "name": "TEMPORAL · MIGRAR A NATIVO · Adaptador generación de imágenes",
        "replacement_runtime": "factory_image_native_contract.py",
        "legacy_status": "inactive",
        "migration": "MIGRATE_TO_NATIVE_RUNTIME_KEEP_INACTIVE",
        "inputs": ("run_id", "format", "prompt", "environment", "production_order_id"),
        "old_statuses": ("CREATED", "REUSED", "BLOCKED_DUPLICATES"),
        "paid_provider_present_in_old": True,
        "old_provider": "gpt-image-1",
        "old_external_mutations": ("OpenAI image generation", "Google Drive upload", "Notion page create/update"),
        "old_external_action_allowed": False,
    },
}


def get_factory_legacy_contract(scenario_id: int) -> dict:
    try:
        return FACTORY_LEGACY_MAP[scenario_id]
    except KeyError as exc:
        raise ValueError("unknown factory legacy scenario") from exc


def assess_factory_migration_readiness(*, scenario_id: int, live_contract_captured: bool,
                                       runtime_target_exists: bool, replay_parity_green: bool,
                                       rollback_proven: bool) -> dict:
    item = get_factory_legacy_contract(scenario_id)
    gates = {
        "live_contract_captured": live_contract_captured,
        "runtime_target_exists": runtime_target_exists,
        "replay_parity_green": replay_parity_green,
        "rollback_proven": rollback_proven,
    }
    green = all(gates.values())
    return {
        "scenario_id": scenario_id,
        "migration": item["migration"],
        "gates": gates,
        "green_code_ci": green,
        "legacy_must_remain_inactive": True,
        "delete_legacy_allowed": False,
        "autoactivate_legacy_allowed": False,
        "external_action_allowed": False,
        "prod_cutover_allowed": False,
    }


def all_legacy_fail_closed() -> bool:
    return all(
        item["legacy_status"] == "inactive" and item["old_external_action_allowed"] is False
        for item in FACTORY_LEGACY_MAP.values()
    )
