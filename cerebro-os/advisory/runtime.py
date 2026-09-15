from __future__ import annotations

from collections.abc import Callable, Mapping

from .capabilities import engine_dependencies
from .coordinator import coordinate
from .models import AdvisoryCase, AdvisoryDecision, DomainOpinion
from .router import route_case

DomainHandler = Callable[[AdvisoryCase, tuple[str, ...]], DomainOpinion]


def execute_case(
    case: AdvisoryCase,
    handlers: Mapping[str, DomainHandler],
    audit_refs: tuple[str, ...] = (),
) -> AdvisoryDecision:
    """Route and coordinate one advisory case in a shared fail-closed runtime.

    No external side effects are performed here. A caller must inject an
    explicit handler for every routed domain. Missing handlers are a technical
    BLOCKED condition, not a HUMAN_REQUIRED exception.
    """

    routed_domains = route_case(case)
    missing_handlers = [domain for domain in routed_domains if domain not in handlers]
    if missing_handlers:
        raise RuntimeError(f"missing advisory handlers: {missing_handlers}")

    opinions: list[DomainOpinion] = []
    for domain in routed_domains:
        dependencies = engine_dependencies(domain)
        opinion = handlers[domain](case, dependencies)
        if opinion.domain != domain:
            raise ValueError(
                f"handler domain mismatch: routed={domain} returned={opinion.domain}"
            )
        opinion.validate()
        opinions.append(opinion)

    return coordinate(
        case_id=case.case_id,
        routed_domains=routed_domains,
        opinions=tuple(opinions),
        audit_refs=audit_refs,
    )
