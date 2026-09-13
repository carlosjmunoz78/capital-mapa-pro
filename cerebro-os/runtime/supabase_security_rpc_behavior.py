from __future__ import annotations

READ_ONLY_RPCS = (
    "fenix_prod_ana_knowledge_answer_user",
    "fenix_prod_chat_conversations_user",
    "fenix_prod_chat_list_user",
    "fenix_prod_chat_list_v2_user",
    "fenix_prod_chat_people_user",
    "fenix_prod_notifications_list_user",
    "fenix_prod_profile_get_user",
    "fenix_prod_profile_socials_get_user",
    "fenix_prod_session_context",
)

MUTATING_RPCS = (
    "fenix_prod_chat_attachment_add_user",
    "fenix_prod_chat_attachment_add_v2_user",
    "fenix_prod_chat_conversation_create_user",
    "fenix_prod_chat_group_create_user",
    "fenix_prod_chat_send_user",
    "fenix_prod_chat_send_v2_user",
    "fenix_prod_contact_create",
    "fenix_prod_contact_create_v2",
    "fenix_prod_exp_create",
    "fenix_prod_exp_update",
    "fenix_prod_inmo_followup_update_v1",
    "fenix_prod_notification_mark_user",
    "fenix_prod_profile_socials_update_user",
    "fenix_prod_profile_update_user",
    "fenix_prod_sign_create",
)

AUTHZ_GUARDS_OBSERVED = (
    "auth_uid_required",
    "active_actor_resolution",
    "role_or_membership_or_ownership_checks",
    "input_validation",
)


def assess_rpc_behavior_surface() -> dict:
    all_rpcs = READ_ONLY_RPCS + MUTATING_RPCS
    return {
        "rpc_count": len(all_rpcs),
        "read_only_count": len(READ_ONLY_RPCS),
        "mutating_count": len(MUTATING_RPCS),
        "unique": len(set(all_rpcs)) == len(all_rpcs),
        "authenticated_execute_observed": True,
        "security_definer_observed": True,
        "internal_authz_guards_observed": AUTHZ_GUARDS_OBSERVED,
        "automatic_revoke_allowed": False,
        "automatic_security_invoker_conversion_allowed": False,
        "automatic_prod_mutation_allowed": False,
        "mutator_parity_required_before_change": True,
        "human_reason": "HIGH_RISK",
        "status": "BEHAVIOR_CLASSIFIED_PARITY_BEFORE_REMEDIATION",
    }
