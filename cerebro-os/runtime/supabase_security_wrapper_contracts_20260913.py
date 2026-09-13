from __future__ import annotations

# Proposed server-wrapper contracts only. These are design contracts for LAB/CI and
# do not create or replace any PROD database function.

WRAPPER_CONTRACTS = {
    "fenix_prod_chat_attachment_add_user": {
        "proposed_server": "fenix_prod_chat_attachment_add_server",
        "actor_context": "p_actor_code",
        "preserve": ("message_ownership", "storage_path_scope", "mime_allowlist", "20mb_size_limit", "duplicate_conflict"),
    },
    "fenix_prod_chat_attachment_add_v2_user": {
        "proposed_server": "fenix_prod_chat_attachment_add_v2_server",
        "actor_context": "p_actor_code",
        "preserve": ("conversation_membership", "message_ownership", "storage_path_scope", "mime_allowlist", "20mb_size_limit", "duplicate_conflict"),
    },
    "fenix_prod_chat_conversation_create_user": {
        "proposed_server": "fenix_prod_chat_conversation_create_server",
        "actor_context": "p_actor_code",
        "preserve": ("active_member_validation", "direct_conversation_reuse", "group_title_limit", "member_deduplication"),
    },
    "fenix_prod_chat_group_create_user": {
        "proposed_server": "fenix_prod_chat_group_create_server",
        "actor_context": "p_actor_code",
        "preserve": ("active_member_validation", "group_creation", "group_title_limit", "member_deduplication"),
    },
    "fenix_prod_chat_send_v2_user": {
        "proposed_server": "fenix_prod_chat_send_v2_server",
        "actor_context": "p_actor_code",
        "preserve": ("conversation_membership", "body_limit", "idempotency_key", "conversation_updated_at"),
    },
    "fenix_prod_contact_create": {
        "proposed_server": "fenix_prod_contact_create_server",
        "actor_context": "p_actor_code",
        "preserve": ("role_scope", "zone_scope", "duplicate_detection", "destination_routing", "consent_flag"),
    },
    "fenix_prod_contact_create_v2": {
        "proposed_server": "fenix_prod_contact_create_v2_server",
        "actor_context": "p_actor_code",
        "preserve": ("role_scope", "multi_email_phone_normalization", "duplicate_detection", "v1_create_semantics"),
    },
    "fenix_prod_exp_create": {
        "proposed_server": "fenix_prod_exp_create_server",
        "actor_context": "p_actor_code",
        "preserve": ("role_scope", "owner_scope", "client_reuse", "15_minute_duplicate_guard", "participant_link", "consent_flag"),
    },
    "fenix_prod_inmo_followup_update_v1": {
        "proposed_server": "fenix_prod_inmo_followup_update_v1_server",
        "actor_context": "p_actor_code",
        "preserve": ("role_scope", "visitador_owner_or_zone_scope", "expected_version", "notes_and_next_contact_write_set"),
    },
    "fenix_prod_notification_mark_user": {
        "proposed_server": "fenix_prod_notification_mark_server",
        "actor_context": "p_actor_code",
        "preserve": ("task_owner_or_direccion_scope", "action_allowlist", "read_dismiss_restore_semantics"),
    },
    "fenix_prod_profile_socials_update_user": {
        "proposed_server": "fenix_prod_profile_socials_update_server",
        "actor_context": "p_actor_code",
        "preserve": ("social_field_limits", "actor_profile_upsert", "activity_log_write"),
    },
    "fenix_prod_profile_update_user": {
        "proposed_server": "fenix_prod_profile_update_self_server",
        "actor_context": "p_actor_code",
        "preserve": ("display_name_required", "username_uniqueness", "birth_date_validation", "actor_profile_full_write_set", "activity_log_write"),
        "note": "Existing fenix_prod_profile_update_server is not equivalent and must remain untouched.",
    },
    "fenix_prod_sign_create": {
        "proposed_server": "fenix_prod_sign_create_server",
        "actor_context": "p_actor_code",
        "preserve": ("direccion_or_financiero_scope", "financiero_owner_scope", "active_signature_conflict", "signature_state_derivation", "signature_write_set"),
        "human_required": "SIGNATURE_REQUIRED",
    },
}


def assess() -> dict:
    names = tuple(WRAPPER_CONTRACTS)
    return {
        "contract_count": len(names),
        "all_have_actor_context": all(v.get("actor_context") == "p_actor_code" for v in WRAPPER_CONTRACTS.values()),
        "all_have_preservation_contract": all(bool(v.get("preserve")) for v in WRAPPER_CONTRACTS.values()),
        "profile_existing_server_reuse_forbidden": "not equivalent" in WRAPPER_CONTRACTS["fenix_prod_profile_update_user"]["note"].lower(),
        "signature_required_preserved": WRAPPER_CONTRACTS["fenix_prod_sign_create"].get("human_required") == "SIGNATURE_REQUIRED",
        "prod_function_created": False,
        "prod_function_replaced": False,
        "automatic_prod_mutation_allowed": False,
        "status": "THIRTEEN_SERVER_WRAPPER_CONTRACTS_DEFINED_IMPLEMENTATION_PENDING",
    }
