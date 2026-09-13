from __future__ import annotations

# Read-only classification captured from live fenix-capital-prod on 2026-09-13.
# This file records implementation shape only. It authorizes no PROD mutation.

TARGETS = {
    "fenix_prod_chat_send_user": {"shape": "DIRECT_DELEGATION", "server_target": "fenix_prod_chat_send_server", "parity_status": "STRUCTURAL_DELEGATION_PROVEN"},
    "fenix_prod_exp_update": {"shape": "DIRECT_DELEGATION", "server_target": "fenix_prod_exp_update_server", "parity_status": "STRUCTURAL_DELEGATION_PROVEN"},
    "fenix_prod_profile_update_user": {"shape": "DISTINCT_IMPLEMENTATION", "server_target": "fenix_prod_profile_update_server", "parity_status": "NOT_EQUIVALENT_BY_INSPECTION"},
    "fenix_prod_chat_attachment_add_user": {"shape": "DIRECT_USER_IMPLEMENTATION", "server_target": None, "parity_status": "SERVER_EQUIVALENT_NOT_IDENTIFIED"},
    "fenix_prod_chat_attachment_add_v2_user": {"shape": "DIRECT_USER_IMPLEMENTATION", "server_target": None, "parity_status": "SERVER_EQUIVALENT_NOT_IDENTIFIED"},
    "fenix_prod_chat_conversation_create_user": {"shape": "DIRECT_USER_IMPLEMENTATION", "server_target": None, "parity_status": "SERVER_EQUIVALENT_NOT_IDENTIFIED"},
    "fenix_prod_chat_group_create_user": {"shape": "DIRECT_USER_IMPLEMENTATION", "server_target": None, "parity_status": "SERVER_EQUIVALENT_NOT_IDENTIFIED"},
    "fenix_prod_chat_send_v2_user": {"shape": "DIRECT_USER_IMPLEMENTATION", "server_target": None, "parity_status": "SERVER_EQUIVALENT_NOT_IDENTIFIED"},
    "fenix_prod_contact_create": {"shape": "DIRECT_USER_IMPLEMENTATION", "server_target": None, "parity_status": "SERVER_EQUIVALENT_NOT_IDENTIFIED"},
    "fenix_prod_contact_create_v2": {"shape": "COMPOSES_USER_MUTATOR", "server_target": None, "parity_status": "SERVER_EQUIVALENT_NOT_IDENTIFIED"},
    "fenix_prod_exp_create": {"shape": "DIRECT_USER_IMPLEMENTATION", "server_target": None, "parity_status": "SERVER_EQUIVALENT_NOT_IDENTIFIED"},
    "fenix_prod_inmo_followup_update_v1": {"shape": "DIRECT_USER_IMPLEMENTATION", "server_target": None, "parity_status": "SERVER_EQUIVALENT_NOT_IDENTIFIED"},
    "fenix_prod_notification_mark_user": {"shape": "DIRECT_USER_IMPLEMENTATION", "server_target": None, "parity_status": "SERVER_EQUIVALENT_NOT_IDENTIFIED"},
    "fenix_prod_profile_socials_update_user": {"shape": "DIRECT_USER_IMPLEMENTATION", "server_target": None, "parity_status": "SERVER_EQUIVALENT_NOT_IDENTIFIED"},
    "fenix_prod_sign_create": {"shape": "DIRECT_USER_IMPLEMENTATION", "server_target": None, "parity_status": "SIGNATURE_REQUIRED_AND_SERVER_EQUIVALENT_NOT_IDENTIFIED"},
}


def assess() -> dict:
    direct = tuple(k for k, v in TARGETS.items() if v["shape"] == "DIRECT_DELEGATION")
    distinct = tuple(k for k, v in TARGETS.items() if v["shape"] == "DISTINCT_IMPLEMENTATION")
    no_server = tuple(k for k, v in TARGETS.items() if v["server_target"] is None)
    return {
        "target_count": len(TARGETS),
        "direct_delegation_count": len(direct),
        "distinct_implementation_count": len(distinct),
        "without_identified_server_equivalent_count": len(no_server),
        "direct_delegations": direct,
        "distinct_implementations": distinct,
        "automatic_prod_mutation_allowed": False,
        "grant_revoke_allowed": False,
        "retirement_allowed": False,
        "security_green": False,
        "status": "IMPLEMENTATION_SHAPE_CLASSIFIED_PARITY_AND_CALLER_CLOSURE_PENDING",
    }
