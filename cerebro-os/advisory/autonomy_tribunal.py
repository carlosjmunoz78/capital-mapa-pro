from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .e2e_validation import E2EValidationResult
from .models import CANONICAL_HUMAN_EXCEPTIONS
from .observability import advisory_health


@dataclass(frozen=True)
class AdvisoryAutonomyVerdict:
    verdict: str
    gates: dict[str, bool]
    blockers: tuple[str, ...]
    preprod_advisory_autonomy_candidate: bool
    capability_green_global: bool
    autonomy_green: bool
    prod_enabled: bool


def adjudicate_advisory_autonomy(
    *,
    e2e: E2EValidationResult,
    source_lock_summary: Mapping[str, object],
    capability_runtime: Mapping[str, object],
) -> AdvisoryAutonomyVerdict:
    """Adjudicate Advisory readiness without promoting global autonomy or PROD.

    Passing this tribunal proves the isolated Advisory PREPROD candidate meets
    the Block-D gates. It intentionally does not flip global capability,
    autonomy or PROD flags; those are separate promotion decisions.
    """

    health = advisory_health()
    gates = {
        "e2e_green": e2e.green,
        "representative_12_domains": len(e2e.representative_domains) == 12,
        "sources_bound_12": (
            int(source_lock_summary.get("domains", 0)) == 12
            and int(source_lock_summary.get("bound", 0)) == 12
            and int(source_lock_summary.get("missing_artifact", 1)) == 0
        ),
        "canonical_human_exceptions": len(CANONICAL_HUMAN_EXCEPTIONS) == 8,
        "health_readiness_green": health.get("readiness") == "GREEN",
        "persistent_preprod": bool(capability_runtime.get("persistent_preprod_environment")),
        "preprod_functional_validation": bool(
            capability_runtime.get("persistent_preprod_functional_validation")
        ),
        "preprod_domain_coverage_12": int(
            capability_runtime.get("persistent_preprod_domain_coverage", 0)
        ) == 12,
        "external_writes_disabled": bool(
            capability_runtime.get("persistent_preprod_external_writes_disabled")
        ),
        "app_crm_access_disabled": bool(
            capability_runtime.get("persistent_preprod_app_crm_access_disabled")
        ),
        "prod_credentials_disabled": bool(
            capability_runtime.get("persistent_preprod_prod_credentials_disabled")
        ),
        "customer_data_disabled": bool(
            capability_runtime.get("persistent_preprod_customer_data_disabled")
        ),
    }
    blockers = tuple(name for name, passed in gates.items() if not passed)
    candidate = not blockers
    return AdvisoryAutonomyVerdict(
        verdict="PASS_PREPROD_ADVISORY_AUTONOMY" if candidate else "BLOCKED",
        gates=gates,
        blockers=blockers,
        preprod_advisory_autonomy_candidate=candidate,
        capability_green_global=False,
        autonomy_green=False,
        prod_enabled=False,
    )
