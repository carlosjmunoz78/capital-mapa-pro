from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .capabilities import CAPABILITY_REGISTRY
from .models import AdvisoryCase, EvidenceRef, Territory
from .router import route_case

ADVISORY_COMPONENT_ID = "PROFESSIONAL_ADVISORY"


def canonical_advisory_engine_ids() -> frozenset[str]:
    return frozenset(
        engine_id
        for capability in CAPABILITY_REGISTRY.values()
        for engine_id in capability.engine_ids
    )


@dataclass(frozen=True)
class AdvisoryGatewayRequest:
    """Versioned multi-company gateway contract for Professional Advisory.

    The orchestrator is represented by ``component_id``. ``engine_id`` always
    refers to a canonical underlying logical engine. Keeping those identities
    separate preserves the manifest contract (the orchestrator is not itself a
    new engine) and prevents fail-open routing through a pseudo engine ID.
    """

    company_id: str
    component_id: str
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
            self.component_id,
            self.engine_id,
            self.version,
            self.case_id,
            self.correlation_id,
            self.requested_service,
        )
        if not all(value.strip() for value in required):
            raise ValueError(
                "company_id, component_id, engine_id, version, case_id, correlation_id and requested_service required"
            )
        if self.component_id != ADVISORY_COMPONENT_ID:
            raise ValueError(f"invalid advisory component_id: {self.component_id}")
        if self.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("invalid environment")
        if self.engine_id not in canonical_advisory_engine_ids():
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
    """Resolve explicit/automatic routing with fail-closed engine binding."""

    routed = route_case(request.to_case())
    compatible = any(
        request.engine_id in CAPABILITY_REGISTRY[domain].engine_ids
        for domain in routed
    )
    if not compatible:
        raise ValueError(
            f"engine_id {request.engine_id} is not compatible with routed domains {routed}"
        )
    return routed
