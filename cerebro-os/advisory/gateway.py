from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .models import AdvisoryCase, EvidenceRef, Territory
from .router import route_case


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

    ``route_case`` already combines explicit domains, service hints and
    cross-domain triggers. Unknown or empty routes fail closed.
    """

    return route_case(request.to_case())
