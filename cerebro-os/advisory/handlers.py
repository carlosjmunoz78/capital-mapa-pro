from __future__ import annotations

from collections.abc import Mapping

from .binding_readiness import binding_readiness
from .models import AdvisoryCase, DomainOpinion


def _tuple_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, (tuple, list)):
        return tuple(str(x) for x in value if str(x).strip())
    return ()


def evidence_bound_handler(domain: str):
    """Create a fail-closed LAB handler bound to all canonical dependencies.

    The case must supply facts.engine_evidence as a mapping of engine_id to one
    or more evidence refs and domain_source_refs as a mapping of domain to source
    refs. This adapter proves routing/binding/evidence discipline; it does not
    claim that every underlying engine has completed a production-grade action.
    """

    readiness = binding_readiness(domain)
    if readiness.status != "FULLY_BINDABLE":
        raise RuntimeError(f"domain not fully bindable: {domain}")

    def _handler(case: AdvisoryCase, dependencies: tuple[str, ...]) -> DomainOpinion:
        if case.environment != "LAB":
            return DomainOpinion(
                domain=domain,
                status="BLOCKED",
                summary="LAB handler cannot execute outside LAB",
                source_refs=(),
                risks=("environment_not_lab",),
            )
        if dependencies != readiness.required_engine_ids:
            raise ValueError(f"dependency mismatch for {domain}")

        raw_engine_evidence = case.facts.get("engine_evidence", {})
        if not isinstance(raw_engine_evidence, Mapping):
            raw_engine_evidence = {}
        missing = tuple(
            engine_id
            for engine_id in dependencies
            if not _tuple_strings(raw_engine_evidence.get(engine_id))
        )

        raw_domain_sources = case.facts.get("domain_source_refs", {})
        if not isinstance(raw_domain_sources, Mapping):
            raw_domain_sources = {}
        source_refs = _tuple_strings(raw_domain_sources.get(domain))

        if missing or not source_refs:
            risks = tuple(f"missing_engine_evidence:{engine_id}" for engine_id in missing)
            if not source_refs:
                risks += ("missing_domain_source_refs",)
            return DomainOpinion(
                domain=domain,
                status="BLOCKED",
                summary="Required LAB evidence is incomplete",
                source_refs=source_refs,
                risks=risks,
            )

        return DomainOpinion(
            domain=domain,
            status="GREEN",
            summary="All canonical LAB dependency evidence is present",
            source_refs=source_refs,
            next_actions=("continue_case_coordination",),
        )

    return _handler


def build_lab_handlers(domains: tuple[str, ...]) -> dict[str, object]:
    return {domain: evidence_bound_handler(domain) for domain in domains}
