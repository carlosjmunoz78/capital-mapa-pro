from __future__ import annotations

# Fail-closed policy for social networks whose analytics scenarios are intentionally
# inactive and therefore have no retained metric executions. Defining this policy
# does NOT approve absence and does NOT activate any Make scenario.

TARGETS = {
    "linkedin": {"scenario_id": 9522860, "retained_runs": 0, "configured_read_only": True},
    "youtube": {"scenario_id": 9537666, "retained_runs": 0, "configured_read_only": True},
}

ALLOWED_REASONS = {
    "INTENTIONALLY_INACTIVE",
    "PROVIDER_NO_DATA",
    "ACCOUNT_NOT_READY",
}


def evaluate_absence_policy(*, network: str, reason: str, explicitly_approved: bool) -> dict:
    if network not in TARGETS:
        raise ValueError("unknown_network")
    if reason not in ALLOWED_REASONS:
        raise ValueError("unsupported_absence_reason")
    target = TARGETS[network]
    no_retained_runs = target["retained_runs"] == 0
    green_as_approved_absence = bool(
        no_retained_runs
        and target["configured_read_only"]
        and reason == "INTENTIONALLY_INACTIVE"
        and explicitly_approved
    )
    return {
        "network": network,
        "scenario_id": target["scenario_id"],
        "retained_runs": target["retained_runs"],
        "configured_read_only": target["configured_read_only"],
        "reason": reason,
        "explicitly_approved": bool(explicitly_approved),
        "approved_absence_green": green_as_approved_absence,
        "scenario_activation_performed": False,
        "automatic_activation_allowed": False,
        "status": "APPROVED_ABSENCE" if green_as_approved_absence else "ABSENCE_POLICY_PENDING_APPROVAL",
    }


def assess_current() -> dict:
    rows = {
        network: evaluate_absence_policy(
            network=network,
            reason="INTENTIONALLY_INACTIVE",
            explicitly_approved=False,
        )
        for network in TARGETS
    }
    return {
        "targets": rows,
        "policy_defined": True,
        "all_approved": all(row["approved_absence_green"] for row in rows.values()),
        "human_approval_required": True,
        "make_mutation_performed": False,
        "status": "POLICY_DEFINED_APPROVAL_PENDING",
    }
