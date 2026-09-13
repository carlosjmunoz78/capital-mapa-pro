from __future__ import annotations

MODULES = {
    "APP_003_expedientes": {
        "server_contracts": (
            "fenix_prod_exp_list_server", "fenix_prod_exp_people_server", "fenix_prod_exp_person_create_server",
            "fenix_prod_exp_person_read_server", "fenix_prod_exp_person_update_server", "fenix_prod_exp_stage_server",
            "fenix_prod_exp_update_server", "fenix_prod_expediente_actions_server", "fenix_prod_expediente_consistency_server",
            "fenix_prod_expediente_workspace_server",
        ),
        "service_role_only": True,
    },
    "APP_004_tasks_notifications": {
        "server_contracts": ("fenix_prod_task_create_server", "fenix_prod_task_get_server", "fenix_prod_task_update_server", "fenix_prod_reassign_task_server"),
        "service_role_only": True,
        "notifications_user_rpc_still_direct": True,
    },
    "APP_005_documents": {
        "server_contracts": (
            "fenix_prod_doc_prepare", "fenix_prod_doc_finalize", "fenix_prod_document_access_server",
            "fenix_prod_document_edit_server", "fenix_prod_document_get_server", "fenix_prod_document_list_server",
            "fenix_prod_document_update_server", "fenix_prod_document_versions_server", "fenix_prod_document_view_path_server",
        ),
        "service_role_only": True,
    },
    "APP_006_signatures": {
        "server_contracts": (
            "fenix_prod_sign_by_exp_server", "fenix_prod_sign_close_server", "fenix_prod_sign_confirm_server",
            "fenix_prod_sign_history_server", "fenix_prod_sign_list_server", "fenix_prod_sign_schedule_server", "fenix_prod_sign_scope_server",
        ),
        "service_role_only": True,
        "create_server_wrapper_missing": True,
    },
    "APP_007_communications": {
        "server_contracts": (
            "fenix_prod_communications_authorize_server", "fenix_prod_communications_list_server",
            "fenix_prod_communications_prepare_server", "fenix_prod_communications_send_claim_server",
            "fenix_prod_communications_send_finalize_server", "fenix_prod_communications_simulate_server",
        ),
        "service_role_only": True,
    },
    "APP_008_reports": {
        "server_contracts": ("fenix_prod_reports_server", "fenix_prod_appraisal_report_server"),
        "service_role_only": True,
    },
    "CRM_002_sync_consistency": {
        "server_contracts": ("fenix_prod_crm_sync_server", "fenix_prod_directory_personal_server", "fenix_prod_directory_sync_server"),
        "service_role_only": True,
    },
}


def assess() -> dict:
    structural = {k: bool(v["server_contracts"]) and v["service_role_only"] for k, v in MODULES.items()}
    return {
        "structural_contract_green": structural,
        "all_structural_contracts_green": all(structural.values()),
        "APP_004_runtime_migration_complete": not MODULES["APP_004_tasks_notifications"]["notifications_user_rpc_still_direct"],
        "APP_006_create_contract_complete": not MODULES["APP_006_signatures"]["create_server_wrapper_missing"],
        "prod_write_performed": False,
        "status": "APP_CRM_MODULE_CONTRACTS_GREEN_RUNTIME_MIGRATION_PARTIAL",
    }
