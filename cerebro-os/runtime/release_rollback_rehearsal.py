from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RehearsalEvidence:
    current_ref: str
    target_ref: str
    build_valid: bool = False
    contract_valid: bool = False
    smoke_valid: bool = False
    external_mutation: bool = False


def assess_release_rollback_rehearsal(evidence: RehearsalEvidence) -> dict:
    if not evidence.current_ref.strip() or not evidence.target_ref.strip():
        raise ValueError("current_ref and target_ref are required")
    checks = {
        "current_ref_pinned": bool(evidence.current_ref.strip()),
        "target_ref_pinned": bool(evidence.target_ref.strip()),
        "build_valid": evidence.build_valid,
        "contract_valid": evidence.contract_valid,
        "smoke_valid": evidence.smoke_valid,
        "non_destructive": not evidence.external_mutation,
    }
    green = all(checks.values())
    return {
        "checks": checks,
        "rollback_rehearsal_green": green,
        "external_mutation_allowed": False,
        "automatic_promotion_allowed": False,
        "human_reason": None if green else "HIGH_RISK",
        "status": "ROLLBACK_REHEARSAL_GREEN_NON_DESTRUCTIVE" if green else "ROLLBACK_REHEARSAL_INCOMPLETE",
    }


if __name__ == "__main__":
    evidence = RehearsalEvidence(
        current_ref="ci-current-ref",
        target_ref="ci-known-good-ref",
        build_valid=True,
        contract_valid=True,
        smoke_valid=True,
    )
    result = assess_release_rollback_rehearsal(evidence)
    if not result["rollback_rehearsal_green"]:
        raise SystemExit(1)
    print(result["status"])
