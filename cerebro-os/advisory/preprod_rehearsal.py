from __future__ import annotations

from dataclasses import replace
from collections.abc import Mapping

from .binding_readiness import binding_readiness
from .models import AdvisoryCase, DomainOpinion, CANONICAL_DOMAINS
from .representative_cases import REPRESENTATIVE_CASE_SPECS, build_representative_case
from .runtime import execute_case


def _tuple_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, (tuple, list)):
        return tuple(str(x) for x in value if str(x).strip())
    return ()


def preprod_rehearsal_handler(domain: str):
    """Fail-closed PREPROD rehearsal handler.

    This handler never performs external writes. It proves that a PREPROD-shaped
    case can traverse the advisory runtime only when isolation controls and all
    dependency/source evidence are present.
    """

    readiness = binding_readiness(domain)
    if readiness.status != "FULLY_BINDABLE":
        raise RuntimeError(f"domain not fully bindable: {domain}")

    def _handler(case: AdvisoryCase, dependencies: tuple[str, ...]) -> DomainOpinion:
        if case.environment != "PREPROD":
            return DomainOpinion(
                domain=domain,
                status="BLOCKED",
                summary="PREPROD rehearsal handler requires PREPROD environment",
                source_refs=(),
                risks=("environment_not_preprod",),
            )
        if dependencies != readiness.required_engine_ids:
            raise ValueError(f"dependency mismatch for {domain}")

        required_isolation = {
            "preprod_rehearsal": True,
            "isolated_runtime": True,
            "external_writes_disabled": True,
            "app_crm_access_disabled": True,
            "prod_credentials_disabled": True,
            "customer_data_disabled": True,
        }
        missing_controls = tuple(
            key for key, expected in required_isolation.items()
            if case.facts.get(key) is not expected
        )

        raw_engine_evidence = case.facts.get("engine_evidence", {})
        if not isinstance(raw_engine_evidence, Mapping):
            raw_engine_evidence = {}
        missing_engine_evidence = tuple(
            engine_id
            for engine_id in dependencies
            if not _tuple_strings(raw_engine_evidence.get(engine_id))
        )

        raw_domain_sources = case.facts.get("domain_source_refs", {})
        if not isinstance(raw_domain_sources, Mapping):
            raw_domain_sources = {}
        source_refs = _tuple_strings(raw_domain_sources.get(domain))

        if missing_controls or missing_engine_evidence or not source_refs:
            risks = tuple(f"missing_isolation_control:{key}" for key in missing_controls)
            risks += tuple(
                f"missing_engine_evidence:{engine_id}"
                for engine_id in missing_engine_evidence
            )
            if not source_refs:
                risks += ("missing_domain_source_refs",)
            return DomainOpinion(
                domain=domain,
                status="BLOCKED",
                summary="PREPROD rehearsal controls or evidence are incomplete",
                source_refs=source_refs,
                risks=risks,
            )

        return DomainOpinion(
            domain=domain,
            status="GREEN",
            summary="Isolated PREPROD rehearsal passed with writes and PROD access disabled",
            source_refs=source_refs,
            next_actions=("continue_preprod_promotion_tribunal",),
        )

    return _handler


def build_preprod_rehearsal_handlers(domains: tuple[str, ...]) -> dict[str, object]:
    return {domain: preprod_rehearsal_handler(domain) for domain in domains}


def build_preprod_rehearsal_case(spec: dict[str, object]) -> AdvisoryCase:
    lab_case = build_representative_case(spec)
    facts = dict(lab_case.facts)
    facts.update(
        {
            "preprod_rehearsal": True,
            "isolated_runtime": True,
            "external_writes_disabled": True,
            "app_crm_access_disabled": True,
            "prod_credentials_disabled": True,
            "customer_data_disabled": True,
        }
    )
    return replace(
        lab_case,
        environment="PREPROD",
        case_id=f"PREPROD-REHEARSAL-{lab_case.case_id}",
        facts=facts,
    )


def run_preprod_rehearsal_suite() -> tuple[object, ...]:
    decisions: list[object] = []
    for spec in REPRESENTATIVE_CASE_SPECS:
        case = build_preprod_rehearsal_case(spec)
        handlers = build_preprod_rehearsal_handlers(case.requested_domains)
        decision = execute_case(
            case,
            handlers,
            audit_refs=(
                f"preprod-rehearsal://{case.case_id}/isolation",
                f"preprod-rehearsal://{case.case_id}/evidence",
                f"preprod-rehearsal://{case.case_id}/rollback-boundary",
            ),
        )
        decision.validate()
        decisions.append(decision)
    return tuple(decisions)


def preprod_rehearsal_passed() -> bool:
    decisions = run_preprod_rehearsal_suite()
    covered = {
        domain
        for decision in decisions
        for domain in decision.domains
    }
    return (
        covered == set(CANONICAL_DOMAINS)
        and all(decision.overall_status == "GREEN" for decision in decisions)
        and all(decision.audit_refs for decision in decisions)
    )
