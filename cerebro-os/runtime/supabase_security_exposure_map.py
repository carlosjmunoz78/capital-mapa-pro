from __future__ import annotations

COMPANY_ID = "fenix_capital"
ENVIRONMENT = "PROD"
PROJECT_ID = "cluhljgonannaafpmblx"

AUTHENTICATED_SECURITY_DEFINER_RPCS = (
    "fenix_prod_ana_knowledge_answer_user",
    "fenix_prod_chat_attachment_add_user",
    "fenix_prod_chat_attachment_add_v2_user",
    "fenix_prod_chat_conversation_create_user",
    "fenix_prod_chat_conversations_user",
    "fenix_prod_chat_group_create_user",
    "fenix_prod_chat_list_user",
    "fenix_prod_chat_list_v2_user",
    "fenix_prod_chat_people_user",
    "fenix_prod_chat_send_user",
    "fenix_prod_chat_send_v2_user",
    "fenix_prod_contact_create",
    "fenix_prod_contact_create_v2",
    "fenix_prod_exp_create",
    "fenix_prod_exp_update",
    "fenix_prod_inmo_followup_update_v1",
    "fenix_prod_notification_mark_user",
    "fenix_prod_notifications_list_user",
    "fenix_prod_profile_get_user",
    "fenix_prod_profile_socials_get_user",
    "fenix_prod_profile_socials_update_user",
    "fenix_prod_profile_update_user",
    "fenix_prod_session_context",
    "fenix_prod_sign_create",
)

POSTGRES_ONLY_RLS_TABLES = (
    "activity_log",
    "actor_profiles",
    "ana_knowledge_cards",
    "chat_attachments",
    "chat_conversation_members",
    "chat_conversations",
    "chat_messages",
    "contact_list_members",
    "contact_lists",
    "daily_report_snapshots",
    "expediente_personas",
    "lead_events",
    "notification_state",
)

RLS_TABLE_COUNT = 40
SERVICE_ROLE_RLS_TABLE_COUNT = 27
POSTGRES_ONLY_RLS_TABLE_COUNT = 13


def assess_live_security_exposure() -> dict:
    return {
        "company_id": COMPANY_ID,
        "environment": ENVIRONMENT,
        "project_id": PROJECT_ID,
        "rls_table_count": RLS_TABLE_COUNT,
        "rls_tables_with_service_role_grant": SERVICE_ROLE_RLS_TABLE_COUNT,
        "rls_tables_without_service_role_grant": POSTGRES_ONLY_RLS_TABLE_COUNT,
        "postgres_only_rls_tables": POSTGRES_ONLY_RLS_TABLES,
        "authenticated_security_definer_rpc_count": len(AUTHENTICATED_SECURITY_DEFINER_RPCS),
        "authenticated_security_definer_rpcs": AUTHENTICATED_SECURITY_DEFINER_RPCS,
        "direct_authenticated_table_grant_observed": False,
        "direct_anon_table_grant_observed": False,
        "security_review_green": False,
        "prod_candidate_allowed": False,
        "automatic_privilege_change_allowed": False,
        "automatic_rls_change_allowed": False,
        "automatic_prod_mutation_allowed": False,
        "human_reason": "HIGH_RISK",
        "status": "LIVE_EXPOSURE_MAPPED_REMEDIATION_PENDING",
    }
