from __future__ import annotations

# Evidence-backed blockers and evidence gaps that cannot be turned green by unsafe autonomous mutation.
# Only canonical HUMAN_REQUIRED codes are allowed here.

CANONICAL_HUMAN_REQUIRED = {
    "LEGAL_REQUIRED",
    "SIGNATURE_REQUIRED",
    "LOW_CONFIDENCE",
    "HIGH_RISK",
    "POLICY_CONFLICT",
    "SECURITY_INCIDENT",
    "MONEY_LIMIT",
    "CUSTOMER_HUMAN_REQUEST",
}

BLOCKERS = {
    "SECURITY_AUTHENTICATED_HTTP_E2E": {
        "group": "SECURITY",
        "status": "PARTIAL_DEDICATED_IDENTITY_AND_READ_PATH_GREEN_WRITE_CLEANUP_OPEN",
        "human_required": "HIGH_RISK",
        "facts": (
            "dedicated_prod_auth_identity_created_by_user_through_supported_dashboard_flow",
            "dedicated_identity_authenticated_in_live_app",
            "notifications_read_path_user_verified_green_in_live_app",
            "raw_auth_users_insertion_forbidden",
            "four_write_target_http_cleanup_routes_not_proven",
        ),
        "unblock": "prove_cleanup_or_non_durable_write_test_strategy_then_complete_authenticated_gateway_write_e2e",
    },
    "SECURITY_CLOUDFLARE_SECRET_EXPOSURE": {
        "group": "SECURITY",
        "status": "SECURITY_INCIDENT_RAW_SECRET_RETURNED_BY_READ_ONLY_INVENTORY",
        "human_required": "SECURITY_INCIDENT",
        "facts": (
            "cloudflare_read_only_inventory_response_included_raw_app_secret_value",
            "secret_value_not_persisted_into_cerebro_docs_or_tests",
            "cloudflare_pages_project_has_only_pages_dev_domain_no_app_fenixcapital_custom_domain",
            "cloudflare_pages_preview_deploy_for_audit_branch_was_skipped_by_preview_policy",
            "app_repository_is_vite_but_cloudflare_pages_build_command_is_next_on_pages",
            "app_repo_default_branch_search_found_no_app_secret_reference",
            "user_elected_to_preserve_current_cloudflare_configuration_for_now",
            "automatic_rotation_rejected_until_dependency_inventory_and_rollback_are_complete",
        ),
        "unblock": "accepted_risk_policy_or_inventory_secret_consumers_then_rotate_through_authorized_channel_and_verify_no_breakage",
    },
    "RECOVERY_PROVIDER_RESTORE": {
        "group": "RECOVERY",
        "status": "BLOCKED_ISOLATED_PROVIDER_TARGET_REQUIRES_COST",
        "human_required": "MONEY_LIMIT",
        "facts": (
            "supabase_main_branch_inventory_main_only",
            "supabase_legacy_branch_inventory_zero",
            "restore_to_new_project_is_paid_plan_feature",
            "restore_to_new_project_creates_new_project_with_additional_monthly_expense",
            "pitr_is_paid_add_on",
            "restoring_over_prod_is_rejected",
        ),
        "unblock": "explicit_money_limit_authorization_or_preexisting_zero_incremental_cost_isolated_provider_target",
    },
    "SECURITY_LEAKED_PASSWORD_PROTECTION": {
        "group": "SECURITY",
        "status": "BLOCKED_SUPPORTED_WRITE_CHANNEL_ABSENT",
        "human_required": "HIGH_RISK",
        "facts": (
            "supabase_leaked_password_protection_available_pro_and_above",
            "supabase_management_api_auth_patch_path_documented",
            "current_supabase_connector_has_no_auth_config_write_action",
            "dashboard_or_pat_bypass_not_attempted",
        ),
        "unblock": "supported_authorized_auth_config_write_channel",
    },
    "OBSERVABILITY_PERSISTENT_PROD_SINK": {
        "group": "OBSERVABILITY",
        "status": "PARTIAL_ZERO_COST_PERSISTENT_SINK_LAB_GREEN_PARALLEL_PROD_WIRING_OPEN",
        "human_required": None,
        "facts": (
            "make_datastore_171764_is_live_shared_core_health_and_dedupe_store_and_was_not_repurposed",
            "make_datastore_172319_is_temp_test_schema_audit_store_and_was_not_repurposed",
            "dedicated_google_sheets_sink_created_without_new_subscription",
            "sink_contract_includes_timestamp_company_id_engine_id_environment_version_kind_run_id_status_message_payload_json",
            "make_on_demand_bridge_scenario_9804649_created_with_existing_google_connection",
            "first_bridge_run_failed_closed_missing_value_input_option",
            "second_mapper_shape_inserted_blank_row_and_was_corrected",
            "final_synthetic_lab_execution_4c9be20f08e54126b4a8a3ab9bb9fd09_success",
            "independent_google_sheets_readback_confirmed_all_ten_fields_persisted",
            "existing_prod_observability_paths_untouched",
        ),
        "unblock": "parallel_wire_selected_prod_engine_family_then_compare_old_new_and_expand_gradually",
    },
    "OBSERVABILITY_YOUTUBE_HEALTH": {
        "group": "OBSERVABILITY",
        "status": "GREEN_CONTROLLED_READ_ONLY_HEALTH_EXECUTION",
        "human_required": None,
        "facts": (
            "previous_connection_verify_400_failure_recorded",
            "youtube_oauth_reauthorized_through_supported_user_flow",
            "connection_14591497_status_ok",
            "manual_execution_bcdc124704c147daafc12363cee431a5_success",
            "execution_completed_three_operations",
            "scenario_contract_read_only_except_health_datastore_write",
        ),
        "unblock": "resolved",
    },
    "FINOPS_EXACT_CURRENT_INVOICES": {
        "group": "FINOPS",
        "status": "PARTIAL_NOTION_CURRENT_AMOUNT_CAPTURED_GCP_MONTHLY_PERIOD_TOTAL_OPEN",
        "human_required": None,
        "facts": (
            "notion_current_billing_ui_amount_user_reported_eur_68_97_for_two_users",
            "notion_plan_rightsizing_deferred_until_after_current_closure_loop",
            "google_cloud_billing_ui_showed_eur_0_34_current_charge_for_fenix_trading_lab_snapshot",
            "google_cloud_billing_ui_showed_eur_0_00_for_fenix_capital_snapshot",
            "google_cloud_monthly_period_total_not_yet_proven",
            "estimation_for_green_forbidden",
        ),
        "unblock": "authoritative_google_cloud_monthly_period_total_or_zero_cost_proof",
    },
}


def validate() -> dict:
    invalid_codes = tuple(
        key
        for key, row in BLOCKERS.items()
        if row["human_required"] is not None
        and row["human_required"] not in CANONICAL_HUMAN_REQUIRED
    )
    return {
        "valid": not invalid_codes,
        "invalid_codes": invalid_codes,
        "blocker_count": len(BLOCKERS),
        "human_gated": tuple(
            key for key, row in BLOCKERS.items() if row["human_required"] is not None
        ),
        "non_human_evidence_gaps": tuple(
            key for key, row in BLOCKERS.items()
            if row["human_required"] is None and not row["status"].startswith("GREEN_")
        ),
    }
