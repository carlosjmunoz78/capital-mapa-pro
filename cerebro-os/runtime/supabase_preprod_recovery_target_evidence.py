from __future__ import annotations

# Live metadata-only evidence captured from Supabase project hnqlnvakzaywtafeiybt.
# This module does NOT authorize destructive restore, overwrite, schema reset, or PROD mutation.
EVIDENCE = {
    "project_id": "hnqlnvakzaywtafeiybt",
    "role": "EXISTING_NON_PROD_PREPROD_TEST_SURFACE",
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
    "restore_executed": False,
    "destructive_action_allowed": False,
    "prod_mutation_allowed": False,
}


def assess_recovery_target() -> dict:
    metadata_supports_non_prod = (
        EVIDENCE["all_observed_public_tables_named_preprod"]
        and EVIDENCE["preprod_or_test_named_functions_present"]
        and EVIDENCE["notion_runtime_test_present"]
        and EVIDENCE["wordpress_preprod_present"]
        and EVIDENCE["seo_executor_preprod_present"]
        and EVIDENCE["app_gateway_test_present"]
        and EVIDENCE["directory_actions_test_present"]
    )
    return {
        **EVIDENCE,
        "metadata_supports_preprod_classification": metadata_supports_non_prod,
        "safe_restore_target_proven": False,
        "provider_restore_green": False,
        "next_required_evidence": (
            "dependency_noncriticality_proven",
            "snapshot_before_restore_proven",
            "isolated_restore_plan_proven",
            "integrity_and_smoke_plan_proven",
        ),
        "status": "PREPROD_TARGET_CANDIDATE_METADATA_GREEN_RESTORE_NOT_EXECUTED",
    }
