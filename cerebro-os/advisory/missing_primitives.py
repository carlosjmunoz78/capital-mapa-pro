from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class FinancialOpsAssessment:  # FINOPS-001
    liquidity_ok: bool
    debt_service_ok: bool
    evidence_refs: tuple[str, ...]

    def decision(self) -> str:
        if not self.evidence_refs:
            return "BLOCKED"
        return "GREEN" if self.liquidity_ok and self.debt_service_ok else "HUMAN_REQUIRED"


@dataclass(frozen=True)
class PropertyAssessment:  # PROP-001
    property_ref: str
    ownership_verified: bool
    encumbrances_checked: bool
    evidence_refs: tuple[str, ...]

    def decision(self) -> str:
        if not self.property_ref.strip() or not self.evidence_refs:
            return "BLOCKED"
        return "GREEN" if self.ownership_verified and self.encumbrances_checked else "HUMAN_REQUIRED"


@dataclass(frozen=True)
class RegistryAssessment:  # REGP-001
    registry_ref: str
    current_extract: bool
    evidence_refs: tuple[str, ...]

    def decision(self) -> str:
        if not self.registry_ref.strip() or not self.evidence_refs:
            return "BLOCKED"
        return "GREEN" if self.current_extract else "AMBER"


@dataclass(frozen=True)
class CadastreAssessment:  # CAT-001
    cadastral_ref: str
    matches_case: bool
    evidence_refs: tuple[str, ...]

    def decision(self) -> str:
        if not self.cadastral_ref.strip() or not self.evidence_refs:
            return "BLOCKED"
        return "GREEN" if self.matches_case else "AMBER"


@dataclass(frozen=True)
class NotarialAssessment:  # NOT-001
    instrument_type: str
    signature_required: bool
    evidence_refs: tuple[str, ...]

    def decision(self) -> tuple[str, str | None]:
        if not self.instrument_type.strip() or not self.evidence_refs:
            return "BLOCKED", None
        if self.signature_required:
            return "HUMAN_REQUIRED", "SIGNATURE_REQUIRED"
        return "GREEN", None


@dataclass(frozen=True)
class ViabilityAssessment:  # VIA-001
    income: Decimal
    committed_outflows: Decimal
    proposed_payment: Decimal
    evidence_refs: tuple[str, ...]

    def ratio(self) -> Decimal:
        if self.income <= 0 or not self.evidence_refs:
            raise ValueError("income and evidence required")
        return (self.committed_outflows + self.proposed_payment) / self.income


@dataclass(frozen=True)
class BankAssessment:  # BNK-001..006 shared deterministic primitive
    bank_engine_id: str
    criteria_met: bool
    evidence_refs: tuple[str, ...]

    def decision(self) -> str:
        if self.bank_engine_id not in {f"BNK-00{i}" for i in range(1, 7)}:
            raise ValueError("unknown bank engine")
        if not self.evidence_refs:
            return "BLOCKED"
        return "GREEN" if self.criteria_met else "AMBER"


@dataclass(frozen=True)
class OfferAssessment:  # OFR-001
    offer_ref: str
    apr: Decimal
    total_cost: Decimal
    evidence_refs: tuple[str, ...]

    def validate(self) -> None:
        if not self.offer_ref.strip() or not self.evidence_refs:
            raise ValueError("offer evidence required")
        if self.apr < 0 or self.total_cost < 0:
            raise ValueError("invalid offer values")


@dataclass(frozen=True)
class RecommendationAssessment:  # REC-001
    recommendation_ref: str
    alternatives_compared: int
    evidence_refs: tuple[str, ...]

    def decision(self) -> str:
        if not self.recommendation_ref.strip() or not self.evidence_refs:
            return "BLOCKED"
        return "GREEN" if self.alternatives_compared >= 2 else "AMBER"


@dataclass(frozen=True)
class AMLAssessment:  # AML-001
    identity_verified: bool
    source_of_funds_checked: bool
    risk_high: bool
    evidence_refs: tuple[str, ...]

    def decision(self) -> tuple[str, str | None]:
        if not self.evidence_refs or not self.identity_verified or not self.source_of_funds_checked:
            return "BLOCKED", None
        if self.risk_high:
            return "HUMAN_REQUIRED", "HIGH_RISK"
        return "GREEN", None


@dataclass(frozen=True)
class KYCAssessment:  # KYC-001
    identity_verified: bool
    beneficial_owner_checked: bool
    evidence_refs: tuple[str, ...]

    def decision(self) -> str:
        if not self.evidence_refs:
            return "BLOCKED"
        return "GREEN" if self.identity_verified and self.beneficial_owner_checked else "BLOCKED"
