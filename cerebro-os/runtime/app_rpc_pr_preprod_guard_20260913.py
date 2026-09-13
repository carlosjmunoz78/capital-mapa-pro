from __future__ import annotations

EVIDENCE = {
    "app_repo": "carlosjmunoz78/fenix-capital-inmo-map",
    "migration_branch": "cerebro-app-crm-rpc-migration-v0-20260913",
    "draft_pr_number": 376,
    "draft_pr_closed": True,
    "draft_pr_merged": False,
    "app_preprod_cancelled_policy": True,
    "legacy_preprod_workflow_triggered_by_pr": True,
    "legacy_preprod_workflow_was_intentional_reactivation": False,
    "main_modified": False,
    "prod_gateway_updated": False,
    "prod_gateway_version_observed": 16,
    "gateway_deploy_attempt_blocked": True,
    "canary_deploy_attempt_blocked": True,
    "authenticated_execute_revoke_allowed": False,
}


def assess() -> dict:
    return {
        "pr_fail_closed": EVIDENCE["draft_pr_closed"] and not EVIDENCE["draft_pr_merged"],
        "app_preprod_reactivated": False,
        "prod_gateway_updated": EVIDENCE["prod_gateway_updated"],
        "authenticated_execute_revoke_allowed": EVIDENCE["authenticated_execute_revoke_allowed"],
        "status": "APP_MIGRATION_BRANCH_PRESERVED_PR_CLOSED_PREPROD_NOT_REACTIVATED",
    }
