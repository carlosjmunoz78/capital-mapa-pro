from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .capabilities import CAPABILITY_REGISTRY
from .models import AdvisoryCase, AdvisoryDecision, EvidenceRef, Territory
from .router import route_case
from .runtime import DomainHandler, execute_case

ADVISORY_COMPONENT_ID = "PROFESSIONAL_ADVISORY"
ADVISORY_EXECUTE_PERMISSION = "advisory:execute"


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
    refers to a canonical underlying logical engine. Actor, context and
    permissions live at the gateway boundary so the preserved AdvisoryCase
    contract does not need a breaking change.
    """

    company_id: str
    component_id: str
    engine_id: str
    environment: str
    version: str
    case_id: str
    correlation_id: str
    actor: Mapping[str, str]
    context: Mapping[str, object]
    permissions: tuple[str, ...]
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
        actor_id = self.actor.get("actor_id", "").strip()
        actor_type = self.actor.get("actor_type", "").strip()
        if not actor_id or not actor_type:
            raise ValueError("actor.actor_id and actor.actor_type required")
        if ADVISORY_EXECUTE_PERMISSION not in self.permissions:
            raise PermissionError(f"missing permission: {ADVISORY_EXECUTE_PERMISSION}")
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


@dataclass(frozen=True)
class AdvisoryGatewayResponse:
    company_id: str
    component_id: str
    engine_id: str
    environment: str
    version: str
    case_id: str
    correlation_id: str
    decision: AdvisoryDecision

    def validate(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.company_id,
                self.component_id,
                self.engine_id,
                self.version,
                self.case_id,
                self.correlation_id,
            )
        ):
            raise ValueError("invalid gateway response identity")
        self.decision.validate()
        if self.decision.case_id != self.case_id:
            raise ValueError("gateway response case_id mismatch")


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


def execute_gateway_request(
    request: AdvisoryGatewayRequest,
    handlers: Mapping[str, DomainHandler],
    audit_refs: tuple[str, ...] = (),
) -> AdvisoryGatewayResponse:
    """Execute Gateway -> Router -> Advisory runtime with traceable response."""

    resolve_gateway_route(request)
    gateway_audit_ref = (
        f"gateway://{request.company_id}/{request.case_id}/{request.correlation_id}"
    )
    decision = execute_case(
        request.to_case(),
        handlers,
        audit_refs=(*audit_refs, gateway_audit_ref),
    )
    response = AdvisoryGatewayResponse(
        company_id=request.company_id,
        component_id=request.component_id,
        engine_id=request.engine_id,
        environment=request.environment,
        version=request.version,
        case_id=request.case_id,
        correlation_id=request.correlation_id,
        decision=decision,
    )
    response.validate()
    return response
