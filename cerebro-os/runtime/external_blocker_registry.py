from __future__ import annotations

# Evidence-backed blockers that cannot be turned green by safe autonomous mutation.
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
        "status": "BLOCKED_SAFE_TEST_IDENTITY_ABSENT",
        "human_required": "HIGH_RISK",
        "facts": (
            "prod_active_auth_linked_actor_carlos_admin_is_real_human",
            "prod_active_auth_linked_actor_belen_dir_is_real_human",
            "ana_system_is_not_auth_linked",
            "no_dedicated_safe_prod_test_identity_proven",
            "raw_auth_users_insertion_forbidden",
        ),
        "unblock": "explicitly_authorized_safe_test_identity_or_equivalent_non_human_prod_test_channel",
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
        "status": "PARTIAL_EXISTING_MAKE_DATASTORE_NOT_SCOPE_COMPATIBLE",
        "human_required": None,
        "facts": (
            "make_team_reachable",
            "make_datastore_171764_is_live_shared_core_health_and_dedupe_store",
            "make_datastore_172319_is_temp_test_schema_audit_store",
            "neither_proven_with_company_id_engine_id_environment_version_kind_schema",
            "reusing_shared_core_store_without_schema_contract_rejected",
            "no_dedicated_datastore_create_or_schema_change_action_exposed_in_current_tool_surface",
            "inactive_scope_probe_scenario_creation_refused_because_make_requires_precreated_datastore",
            "scope_probe_created_no_scenario_and_wrote_no_records",
        ),
        "unblock": "prove_existing_isolated_scope_compatible_store_or_add_safe_zero_cost_persistent_store_contract",
    },
    "OBSERVABILITY_YOUTUBE_HEALTH": {
        "group": "OBSERVABILITY",
        "status": "BLOCKED_CONNECTION_VERIFICATION_400",
        "human_required": "HIGH_RISK",
        "facts": (
            "make_youtube_health_scenario_9537666_activation_attempted",
            "execution_a96383dd40b54b3c91688fe1039a84f4_failed_before_operations",
            "youtube_connection_verification_returned_http_400",
            "execution_consumed_zero_operations_and_zero_credits",
            "scenario_remains_inactive_after_fail_closed_attempt",
        ),
        "unblock": "explicit_secure_youtube_oauth_reauthorization_then_read_only_health_rerun",
    },
    "FINOPS_EXACT_CURRENT_INVOICES": {
        "group": "FINOPS",
        "status": "BLOCKED_AUTHORITATIVE_EXACT_AMOUNTS_NOT_FOUND",
        "human_required": None,
        "facts": (
            "notion_2026_business_list_reference_20_usd_per_member_month_is_not_invoice",
            "notion_exact_current_invoice_eur_not_found",
            "google_cloud_billing_problem_email_found_without_exact_amount",
            "google_cloud_exact_current_amount_not_found",
            "estimation_for_green_forbidden",
        ),
        "unblock": "authoritative_current_invoice_or_billing_ledger_amounts",
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
            key for key, row in BLOCKERS.items() if row["human_required"] is None
        ),
    }
