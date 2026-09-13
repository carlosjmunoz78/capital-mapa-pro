from __future__ import annotations

PROD_PROJECT_ID = "cluhljgonannaafpmblx"
LEGACY_PROJECT_ID = "hnqlnvakzaywtafeiybt"

PROD_RLS_NO_POLICY_TABLES = (
    "activity_log", "actor_profiles", "actors", "ana_correcciones", "ana_knowledge_cards", "bancos",
    "chat_attachments", "chat_conversation_members", "chat_conversations", "chat_messages", "clientes",
    "comunicaciones", "contact_list_members", "contact_lists", "contactos_bancarios", "contactos_inmobiliaria",
    "daily_report_snapshots", "document_change_history", "document_intelligence_runs", "document_origin_links",
    "document_upload_sessions", "document_versions", "documentos", "economia", "envios_banco",
    "expediente_personas", "expedientes", "firma_history", "firmas", "gestiones_b2b", "inmobiliarias",
    "lead_events", "notarias", "notification_state", "ofertas", "personal_directorio", "registros_propiedad",
    "runtime_policies", "tareas", "tasaciones",
)

PROD_AUTHENTICATED_SECURITY_DEFINER_FUNCTIONS = (
    "fenix_prod_ana_knowledge_answer_user", "fenix_prod_chat_attachment_add_user",
    "fenix_prod_chat_attachment_add_v2_user", "fenix_prod_chat_conversation_create_user",
    "fenix_prod_chat_conversations_user", "fenix_prod_chat_group_create_user", "fenix_prod_chat_list_user",
    "fenix_prod_chat_list_v2_user", "fenix_prod_chat_people_user", "fenix_prod_chat_send_user",
    "fenix_prod_chat_send_v2_user", "fenix_prod_contact_create", "fenix_prod_contact_create_v2",
    "fenix_prod_exp_create", "fenix_prod_exp_update", "fenix_prod_inmo_followup_update_v1",
    "fenix_prod_notification_mark_user", "fenix_prod_notifications_list_user", "fenix_prod_profile_get_user",
    "fenix_prod_profile_socials_get_user", "fenix_prod_profile_socials_update_user",
    "fenix_prod_profile_update_user", "fenix_prod_session_context", "fenix_prod_sign_create",
)

LEGACY_RLS_NO_POLICY_COUNT = 30
PROD_EXTENSION_IN_PUBLIC = ("pg_net",)
LEAKED_PASSWORD_PROTECTION_DISABLED_PROJECTS = (LEGACY_PROJECT_ID, PROD_PROJECT_ID)


def assess_security_inventory() -> dict:
    return {
        "prod_rls_no_policy_count": len(PROD_RLS_NO_POLICY_TABLES),
        "prod_security_definer_count": len(PROD_AUTHENTICATED_SECURITY_DEFINER_FUNCTIONS),
        "legacy_rls_no_policy_count": LEGACY_RLS_NO_POLICY_COUNT,
        "extension_in_public_count": len(PROD_EXTENSION_IN_PUBLIC),
        "leaked_password_protection_disabled_count": len(LEAKED_PASSWORD_PROTECTION_DISABLED_PROJECTS),
        "total_findings": len(PROD_RLS_NO_POLICY_TABLES) + len(PROD_AUTHENTICATED_SECURITY_DEFINER_FUNCTIONS) + LEGACY_RLS_NO_POLICY_COUNT + len(PROD_EXTENSION_IN_PUBLIC) + len(LEAKED_PASSWORD_PROTECTION_DISABLED_PROJECTS),
        "live_read_only_audit": True,
        "prod_mutation_performed": False,
        "automatic_remediation_allowed": False,
        "human_reason": "HIGH_RISK",
        "security_green": False,
        "status": "OBJECT_INVENTORY_COMPLETE_REMEDIATION_PENDING",
    }
