from __future__ import annotations

from dataclasses import dataclass

from .models import CANONICAL_DOMAINS


@dataclass(frozen=True)
class DomainCapability:
    domain: str
    engine_ids: tuple[str, ...]
    dedicated_engine: bool = False

    def validate(self) -> None:
        if self.domain not in CANONICAL_DOMAINS:
            raise ValueError(f"unknown advisory domain: {self.domain}")
        if len(set(self.engine_ids)) != len(self.engine_ids):
            raise ValueError(f"duplicate engine dependency in {self.domain}")


# This is a dependency map, not a one-domain/one-server architecture.
# Domains without a dedicated canonical engine reuse shared engines until an
# explicit architecture decision adds a new canonical ID.
CAPABILITY_REGISTRY: dict[str, DomainCapability] = {
    "FISCAL": DomainCapability("FISCAL", ("TAX-001",), dedicated_engine=True),
    "CONTABLE": DomainCapability("CONTABLE", ("ACC-001", "INV-001", "COL-001")),
    "LABORAL": DomainCapability("LABORAL", ("HR-001", "HR-002", "HR-003", "HR-004", "HR-005", "HR-006", "LEG-001")),
    "MERCANTIL": DomainCapability("MERCANTIL", ("LEG-001",)),
    "FINANCIERA": DomainCapability("FINANCIERA", ("TRE-001", "FINOPS-001", "FRC-001")),
    "INMOBILIARIA": DomainCapability("INMOBILIARIA", ("PROP-001", "REGP-001", "CAT-001", "NOT-001")),
    "HIPOTECARIA": DomainCapability("HIPOTECARIA", ("VIA-001", "BNK-001", "BNK-002", "BNK-003", "BNK-004", "BNK-005", "BNK-006", "OFR-001", "REC-001")),
    "SUBVENCIONES_AYUDAS": DomainCapability("SUBVENCIONES_AYUDAS", ("OPP-001", "FRC-001", "LEG-001", "TAX-001")),
    "PROTECCION_DATOS_COMPLIANCE": DomainCapability("PROTECCION_DATOS_COMPLIANCE", ("CMP-002", "DPO-001", "CONS-001", "AML-001", "KYC-001")),
    "EMPRESARIAL_ESTRATEGICA": DomainCapability("EMPRESARIAL_ESTRATEGICA", ("STR-001", "FRC-001", "CAPA-001", "OPP-001", "INN-001", "EXP-001")),
    "PATRIMONIAL": DomainCapability("PATRIMONIAL", ("TAX-001", "LEG-001", "PROP-001", "FRC-001")),
    "JURIDICA_GENERAL": DomainCapability("JURIDICA_GENERAL", ("LEG-001",)),
}


def validate_registry() -> None:
    if set(CAPABILITY_REGISTRY) != set(CANONICAL_DOMAINS):
        missing = sorted(set(CANONICAL_DOMAINS) - set(CAPABILITY_REGISTRY))
        extra = sorted(set(CAPABILITY_REGISTRY) - set(CANONICAL_DOMAINS))
        raise ValueError(f"capability registry mismatch missing={missing} extra={extra}")
    for capability in CAPABILITY_REGISTRY.values():
        capability.validate()


def engine_dependencies(domain: str) -> tuple[str, ...]:
    validate_registry()
    try:
        return CAPABILITY_REGISTRY[domain].engine_ids
    except KeyError as exc:
        raise ValueError(f"unknown advisory domain: {domain}") from exc
