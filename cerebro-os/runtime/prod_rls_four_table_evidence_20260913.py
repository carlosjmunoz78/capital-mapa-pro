from __future__ import annotations

TABLES = {
    "special_cases": {
        "rls_enabled": False,
        "policy_count": 0,
        "rows_observed": 0,
        "default_branch_direct_code_search_matches": 0,
        "server_routes": (
            "fenix_prod_special_case_create_server",
            "fenix_prod_special_case_create_with_people_server",
            "fenix_prod_special_case_get_server",
            "fenix_prod_special_case_list_server",
            "fenix_prod_special_case_update_server",
            "fenix_prod_special_case_confirm_sensitive_server",
        ),
    },
    "special_case_people": {
        "rls_enabled": False,
        "policy_count": 0,
        "rows_observed": 0,
        "default_branch_direct_code_search_matches": 0,
        "server_routes": (
            "fenix_prod_special_case_create_with_people_server",
            "fenix_prod_special_case_people_replace_server",
        ),
    },
    "expediente_stage_history": {
        "rls_enabled": False,
        "policy_count": 0,
        "rows_observed": 24,
        "default_branch_direct_code_search_matches": 0,
        "server_routes": (
            "fenix_prod_exp_stage_server",
            "fenix_prod_exp_update_server",
        ),
    },
    "weekly_report_snapshots": {
        "rls_enabled": False,
        "policy_count": 0,
        "rows_observed": 1,
        "default_branch_direct_code_search_matches": 0,
        "server_routes": (
            "refresh_weekly_report_snapshot_v1",
            "fenix_prod_reports_server",
        ),
    },
}

EDGE_EVIDENCE = {
    "fenix-special-cases-api": {
        "verify_jwt": True,
        "auth_user_lookup": True,
        "actor_context_rpc": True,
        "service_role_backend": True,
        "direction_gate_for_sensitive_confirmation": True,
    },
    "fenix-reports-api": {
        "verify_jwt": True,
        "auth_user_lookup": True,
        "actor_context_rpc": True,
        "service_role_backend": True,
    },
    "fenix-expediente-stage": {
        "verify_jwt": True,
        "auth_user_lookup": True,
        "actor_context_rpc": True,
        "service_role_backend": True,
    },
}


def assess() -> dict:
    all_four_confirmed = len(TABLES) == 4 and all(
        row["rls_enabled"] is False and row["policy_count"] == 0 for row in TABLES.values()
    )
    default_branch_direct_refs_absent = all(
        row["default_branch_direct_code_search_matches"] == 0 for row in TABLES.values()
    )
    server_path_evidence_present = all(row["server_routes"] for row in TABLES.values())
    edge_auth_chain_present = all(
        row.get("verify_jwt") and row.get("auth_user_lookup") and row.get("actor_context_rpc") and row.get("service_role_backend")
        for row in EDGE_EVIDENCE.values()
    )
    return {
        "four_prod_tables_confirmed_rls_off": all_four_confirmed,
        "default_branch_direct_table_refs_absent": default_branch_direct_refs_absent,
        "server_path_evidence_present": server_path_evidence_present,
        "edge_auth_chain_present": edge_auth_chain_present,
        "policy_design_ready_for_isolated_proof": all_four_confirmed and server_path_evidence_present and edge_auth_chain_present,
        "isolated_policy_proof_complete": False,
        "prod_rls_change_allowed": False,
        "rollback_proven_for_prod_rls_change": False,
        "status": "PROD_RLS_POLICY_DESIGN_EVIDENCE_GREEN_ISOLATED_PROOF_PENDING",
    }
