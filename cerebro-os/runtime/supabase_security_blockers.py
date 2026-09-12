from __future__ import annotations

CANONICAL_HUMAN_REASON = "HIGH_RISK"

PROJECT_FINDINGS = {
    "hnqlnvakzaywtafeiybt": {
        "name": "fenix-capital-inmo-map",
        "environment_class": "LEGACY_PREPROD_CORE",
        "rls_enabled_no_policy": 30,
        "authenticated_security_definer_function_executable": 0,
        "extension_in_public": 0,
        "leaked_password_protection_disabled": 1,
    },
    "cluhljgonannaafpmblx": {
        "name": "fenix-capital-prod",
        "environment_class": "PROD",
        "rls_enabled_no_policy": 40,
        "authenticated_security_definer_function_executable": 24,
        "extension_in_public": 1,
        "leaked_password_protection_disabled": 1,
    },
}

REMEDIATION_ORDER = (
    "INVENTORY_AFFECTED_OBJECTS",
    "MAP_CALLERS_AND_PERMISSIONS",
    "CAPTURE_CURRENT_BEHAVIOR_TESTS",
    "DESIGN_PARALLEL_REMEDIATION",
    "TEST_OUTSIDE_PROD",
    "OLD_VS_NEW_COMPARE",
    "PROVE_ROLLBACK",
    "HUMAN_GATED_PROD_CHANGE",
)


def assess_security_blockers() -> dict:
    counts = {
        key: sum(project[key] for project in PROJECT_FINDINGS.values())
        for key in (
            "rls_enabled_no_policy",
            "authenticated_security_definer_function_executable",
            "extension_in_public",
            "leaked_password_protection_disabled",
        )
    }
    total = sum(counts.values())
    prod = PROJECT_FINDINGS["cluhljgonannaafpmblx"]
    prod_blocking = sum(v for k, v in prod.items() if isinstance(v, int)) > 0
    return {
        "finding_counts": counts,
        "finding_total": total,
        "prod_security_blocking": prod_blocking,
        "human_required_reason": CANONICAL_HUMAN_REASON if prod_blocking else None,
        "remediation_order": REMEDIATION_ORDER,
        "automatic_prod_ddl_allowed": False,
        "automatic_auth_policy_change_allowed": False,
        "automatic_extension_move_allowed": False,
        "automatic_function_privilege_change_allowed": False,
        "prod_mutation_performed": False,
        "security_green": total == 0,
        "status": "SECURITY_REVIEW_REQUIRED" if total else "SECURITY_GREEN",
    }
