from __future__ import annotations

TARGETS = {
    "fenix_prod_chat_attachment_add_user": None,
    "fenix_prod_chat_attachment_add_v2_user": None,
    "fenix_prod_chat_conversation_create_user": None,
    "fenix_prod_chat_group_create_user": None,
    "fenix_prod_chat_send_user": "fenix_prod_chat_send_server",
    "fenix_prod_chat_send_v2_user": None,
    "fenix_prod_contact_create": None,
    "fenix_prod_contact_create_v2": None,
    "fenix_prod_exp_create": None,
    "fenix_prod_exp_update": "fenix_prod_exp_update_server",
    "fenix_prod_inmo_followup_update_v1": None,
    "fenix_prod_notification_mark_user": None,
    "fenix_prod_profile_socials_update_user": None,
    "fenix_prod_profile_update_user": "fenix_prod_profile_update_server",
    "fenix_prod_sign_create": None,
}

OBSERVED_SERVER_FINGERPRINTS = {
    "fenix_prod_chat_send_server": "3b3ce0e81f7958214abe3f9a89410650",
    "fenix_prod_exp_update_server": "1b6da6bbd1c3273e3ec8e9e7fc2ce78e",
    "fenix_prod_profile_update_server": "ec329c3eb7a806df8d1d54d472ff4970",
}

PARITY_DIMENSIONS = (
    "authn_identity_equivalence",
    "authz_scope_equivalence",
    "input_validation_equivalence",
    "idempotency_or_versioning_equivalence",
    "write_set_equivalence",
    "error_contract_equivalence",
    "audit_event_equivalence",
    "rollback_path_proven",
)


def assess() -> dict:
    candidates = {k: v for k, v in TARGETS.items() if v}
    missing = tuple(sorted(k for k, v in TARGETS.items() if not v))
    return {
        "target_count": len(TARGETS),
        "direct_server_wrapper_candidate_count": len(candidates),
        "without_direct_name_matched_wrapper_count": len(missing),
        "candidates": candidates,
        "parity_proven_count": 0,
        "automatic_prod_change_allowed": False,
        "status": "THREE_DIRECT_WRAPPER_CANDIDATES_OBSERVED_PARITY_NOT_PROVEN",
    }
