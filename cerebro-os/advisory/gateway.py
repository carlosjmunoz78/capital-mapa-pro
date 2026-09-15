from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .capabilities import CAPABILITY_REGISTRY
from .models import AdvisoryCase, EvidenceRef, Territory
from .router import route_case

ADVISORY_ORCHESTRATOR_ID = "PROFESSIONAL_ADVISORY"


def canonical_advisory_engine_ids() -> frozenset[str]:
    return frozenset(
        engine_id
        for capability in CAPABILITY_REGISTRY.values()
        for engine_id in capability.engine_ids
    )


@dataclass(frozen=True)
class AdvisoryGatewayRequest:
    """Versioned multi-company gateway contract for Professional Advisory.

    This envelope is intentionally separate from ``AdvisoryCase`` so the
    existing case/runtime contract remains backward-compatible. The gateway is
    the only boundary that requires engine_id and correlation_id.
    """

    company_id: str
    engine_id: str
    environment: str
    version: str
    case_id: str
    correlation_id: str
    requested_service: str
    territory: Territory
    facts: Mapping[str, object]
    evidence: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    requested_domains: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        required = (
            self.company_id,
            self.engine_id,
            self.version,
            self.case_id,
            self.correlation_id,
            self.requested_service,
        )
        if not all(value.strip() for value in required):
            raise ValueError(
                "company_id, engine_id, version, case_id, correlation_id and requested_service required"
            )
        if self.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("invalid environment")
        allowed_engine_ids = canonical_advisory_engine_ids() | {ADVISORY_ORCHESTRATOR_ID}
        if self.engine_id not in allowed_engine_ids:
            raise ValueError(f"unknown advisory engine_id: {self.engine_id}")
        self.territory.validate()
        if not self.facts:
            raise ValueError("facts required")
        for ref in self.evidence:
            ref.validate()

    def to_case(self) -> AdvisoryCase:
        self.validate()
        return AdvisoryCase(
            company_id=self.company_id,
            case_id=self.case_id,
            environment=self.environment,
            version=self.version,
            requested_service=self.requested_service,
            territory=self.territory,
            facts=self.facts,
            evidence=self.evidence,
            requested_domains=self.requested_domains,
        )


def resolve_gateway_route(request: AdvisoryGatewayRequest) -> tuple[str, ...]:
    """Validate the boundary contract and resolve explicit/automatic routing.

    ``route_case`` combines explicit domains, service hints and cross-domain
    triggers. Unknown IDs, incompatible engine/domain selections and empty
    routes fail closed.
    """

    routed = route_case(request.to_case())
    if request.engine_id != ADVISORY_ORCHESTRATOR_ID:
        compatible = any(
            request.engine_id in CAPABILITY_REGISTRY[domain].engine_ids
            for domain in routed
        )
        if not compatible:
            raise ValueError(
                f"engine_id {request.engine_id} is not compatible with routed domains {routed}"
            )
    return routed
