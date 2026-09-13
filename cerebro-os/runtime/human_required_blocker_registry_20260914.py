from __future__ import annotations

CANONICAL_REASONS = {
    "LEGAL_REQUIRED",
    "SIGNATURE_REQUIRED",
    "LOW_CONFIDENCE",
    "HIGH_RISK",
    "POLICY_CONFLICT",
    "SECURITY_INCIDENT",
    "MONEY_LIMIT",
    "CUSTOMER_HUMAN_REQUEST",
}

BLOCKERS = (
    {
        "blocker_id": "SECURITY_AUTHENTICATED_HTTP_E2E_IDENTITY",
        "objective": "SECURITY",
        "reason": "HIGH_RISK",
        "required_human_action": "Explicitly authorize creation/use of a dedicated safe PROD test identity, or provide an already-approved non-customer test identity, for authenticated gateway E2E.",
        "automatic_action_allowed": False,
        "why": "Current PROD auth inventory has no test-like user; hijacking a real user session or creating a PROD principal autonomously is prohibited.",
        "unblocks": (
            "authenticated_http_gateway_e2e_for_target_routes_with_safe_identity",
            "rollback_or_non_durable_cleanup_evidence_for_full_http_write_path",
            "selective_retirement_of_only_migrated_legacy_authenticated_execute_after_http_gate",
        ),
    },
    {
        "blocker_id": "RECOVERY_PROVIDER_ISOLATED_RESTORE_TARGET",
        "objective": "RECOVERY",
        "reason": "MONEY_LIMIT",
        "required_human_action": "Only if no zero-cost provider-native restore target becomes available: approve the exact quoted cost of a temporary Supabase branch/project after get_cost confirmation.",
        "automatic_action_allowed": False,
        "why": "PROD has main only and legacy has no branches; creating a branch requires provider cost confirmation.",
        "unblocks": (
            "isolated_provider_non_prod_restore_target_proven_without_unapproved_cost",
            "completed_provider_restore",
            "provider_restore_integrity_check",
        ),
    },
    {
        "blocker_id": "FINOPS_PROVIDER_PAYMENT_ACTION",
        "objective": "FINOPS",
        "reason": "MONEY_LIMIT",
        "required_human_action": "Any payment-method update, charge approval or paid billing-console action remains human-only.",
        "automatic_action_allowed": False,
        "why": "Billing evidence may be read automatically, but payment or money-moving actions are outside autonomous scope.",
        "unblocks": (),
    },
)


def assess() -> dict:
    reasons_valid = all(row["reason"] in CANONICAL_REASONS for row in BLOCKERS)
    no_auto = all(not row["automatic_action_allowed"] for row in BLOCKERS)
    unique = len({row["blocker_id"] for row in BLOCKERS}) == len(BLOCKERS)
    return {
        "blockers": BLOCKERS,
        "canonical_reasons_only": reasons_valid,
        "all_fail_closed": no_auto,
        "unique_blocker_ids": unique,
        "status": "HUMAN_REQUIRED_BLOCKERS_REGISTERED" if reasons_valid and no_auto and unique else "INVALID",
    }
