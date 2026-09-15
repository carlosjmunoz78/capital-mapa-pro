from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

CANONICAL_HUMAN_EXCEPTIONS = {
    "LEGAL_REQUIRED",
    "SIGNATURE_REQUIRED",
    "LOW_CONFIDENCE",
    "HIGH_RISK",
    "POLICY_CONFLICT",
    "SECURITY_INCIDENT",
    "MONEY_LIMIT",
    "CUSTOMER_HUMAN_REQUEST",
}

CANONICAL_DOMAINS = (
    "FISCAL",
    "CONTABLE",
    "LABORAL",
    "MERCANTIL",
    "FINANCIERA",
    "INMOBILIARIA",
    "HIPOTECARIA",
    "SUBVENCIONES_AYUDAS",
    "PROTECCION_DATOS_COMPLIANCE",
    "EMPRESARIAL_ESTRATEGICA",
    "PATRIMONIAL",
    "JURIDICA_GENERAL",
)


@dataclass(frozen=True)
class Territory:
    country: str
    autonomous_community: str | None = None
    province: str | None = None
    municipality: str | None = None

    def validate(self) -> None:
        if not self.country.strip():
            raise ValueError("country required")


@dataclass(frozen=True)
class EvidenceRef:
    source_id: str
    source_version: str
    locator: str
    verified_at: str | None = None

    def validate(self) -> None:
        if not all((self.source_id.strip(), self.source_version.strip(), self.locator.strip())):
            raise ValueError("source_id, source_version and locator required")


@dataclass(frozen=True)
class AdvisoryCase:
    company_id: str
    case_id: str
    environment: str
    version: str
    requested_service: str
    territory: Territory
    facts: Mapping[str, object]
    evidence: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    requested_domains: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if self.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("invalid environment")
        if not all((self.company_id.strip(), self.case_id.strip(), self.version.strip(), self.requested_service.strip())):
            raise ValueError("company_id, case_id, version and requested_service required")
        self.territory.validate()
        if not self.facts:
            raise ValueError("facts required")
        unknown = set(self.requested_domains) - set(CANONICAL_DOMAINS)
        if unknown:
            raise ValueError(f"unknown advisory domains: {sorted(unknown)}")
        for ref in self.evidence:
            ref.validate()


@dataclass(frozen=True)
class DomainOpinion:
    domain: str
    status: str
    summary: str
    source_refs: tuple[str, ...]
    risks: tuple[str, ...] = ()
    deadlines: tuple[str, ...] = ()
    next_actions: tuple[str, ...] = ()
    human_exception: str | None = None

    def validate(self) -> None:
        if self.domain not in CANONICAL_DOMAINS:
            raise ValueError("unknown domain")
        if self.status not in {"GREEN", "AMBER", "RED", "BLOCKED", "HUMAN_REQUIRED"}:
            raise ValueError("invalid opinion status")
        if not self.summary.strip():
            raise ValueError("summary required")
        if self.human_exception is not None and self.human_exception not in CANONICAL_HUMAN_EXCEPTIONS:
            raise ValueError("non-canonical human exception")


@dataclass(frozen=True)
class AdvisoryDecision:
    case_id: str
    domains: tuple[str, ...]
    opinions: tuple[DomainOpinion, ...]
    overall_status: str
    audit_refs: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id required")
        if not self.domains:
            raise ValueError("at least one domain required")
        if set(self.domains) - set(CANONICAL_DOMAINS):
            raise ValueError("unknown decision domain")
        for opinion in self.opinions:
            opinion.validate()
