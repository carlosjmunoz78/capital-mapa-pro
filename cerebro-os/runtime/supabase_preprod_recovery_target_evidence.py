from __future__ import annotations

# Live metadata-only evidence captured from Supabase project hnqlnvakzaywtafeiybt.
# This project contains explicit PREPROD/TEST surfaces, but canonical live dependency
# evidence also classifies it as legacy_core. Therefore it must be preserved and MUST
# NOT be used as a destructive provider-restore target.
EVIDENCE = {
    "project_id": "hnqlnvakzaywtafeiybt",
    "project_name": "fenix-capital-inmo-map",
    "region": "eu-north-1",
    "project_status": "ACTIVE_HEALTHY",
    "role": "EXISTING_NON_PROD_PREPROD_TEST_SURFACE_WITH_LEGACY_CORE_DEPENDENCY",
    "legacy_core_dependency_observed": True,
    "public_table_count_observed": 8,
    "all_observed_public_tables_named_preprod": True,
    "active_edge_functions_observed": 68,
    "preprod_or_test_named_functions_present": True,
    "notion_runtime_test_present": True,
    "wordpress_preprod_present": True,
    "seo_executor_preprod_present": True,
    "app_gateway_test_present": True,
    "directory_actions_test_present": True,
    "sign_e2e_once_present": True,
    "migration_preprod_test_isolation_present": True,
    "migration_preprod_test_api_vertical_present": True,
    "migration_harden_preprod_test_rpc_only_present": True,
    "migration_preprod_service_facade_present": True,
    "migration_preprod_service_facade_regression_guard_present": True,
    "migration_preprod_revoke_legacy_rpc_execute_present": True,
    "generated_types_metadata_captured": True,
    "restore_executed": False,
    "destructive_restore_target_rejected": True,
    "destructive_action_allowed": False,
    "prod_mutation_allowed": False,
}

VALID_SAFE_RESTORE_TARGETS = ("ISOLATED_RESTORE", "PREPROD_CLONE")


def assess_recovery_target() -> dict:
    metadata_supports_preprod = (
        EVIDENCE["project_status"] == "ACTIVE_HEALTHY"
        and EVIDENCE["all_observed_public_tables_named_preprod"]
        and EVIDENCE["preprod_or_test_named_functions_present"]
        and EVIDENCE["notion_runtime_test_present"]
        and EVIDENCE["wordpress_preprod_present"]
        and EVIDENCE["seo_executor_preprod_present"]
        and EVIDENCE["app_gateway_test_present"]
        and EVIDENCE["directory_actions_test_present"]
        and EVIDENCE["migration_preprod_test_isolation_present"]
        and EVIDENCE["migration_harden_preprod_test_rpc_only_present"]
        and EVIDENCE["migration_preprod_service_facade_regression_guard_present"]
        and EVIDENCE["generated_types_metadata_captured"]
    )
    dependency_noncriticality_proven = not EVIDENCE["legacy_core_dependency_observed"]
    return {
        **EVIDENCE,
        "metadata_supports_preprod_classification": metadata_supports_preprod,
        "dependency_noncriticality_proven": dependency_noncriticality_proven,
        "existing_project_safe_for_destructive_restore": False,
        "safe_restore_target_proven": False,
        "provider_restore_green": False,
        "snapshot_before_restore_proven": False,
        "isolated_restore_plan_proven": True,
        "integrity_and_smoke_plan_proven": True,
        "required_restore_target_types": VALID_SAFE_RESTORE_TARGETS,
        "next_required_evidence": (
            "isolated_restore_or_preprod_clone_target_proven",
            "backup_identifier_captured",
            "restore_execution_completed",
            "integrity_check_ref_captured",
            "application_smoke_ref_captured",
            "cleanup_or_retention_ref_captured",
        ),
        "status": "PREPROD_SURFACE_CONFIRMED_LEGACY_CORE_PRESERVE_ISOLATED_CLONE_REQUIRED",
    }
