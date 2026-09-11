from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, Mapping


# DOC-001..004
@dataclass(frozen=True)
class DocumentRecord:
    company_id: str
    document_id: str
    document_type: str
    content_hash: str
    source_ref: str
    confidence: float
    fields: tuple[tuple[str, str], ...] = ()

    def validate(self) -> None:
        if not all((self.company_id.strip(), self.document_id.strip(), self.document_type.strip(), self.content_hash.strip(), self.source_ref.strip())):
            raise ValueError("document identity, hash and provenance required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be normalized")
        if len(dict(self.fields)) != len(self.fields):
            raise ValueError("duplicate document field")

    @property
    def extraction_status(self) -> str:
        self.validate()
        return "GREEN" if self.confidence >= .8 else "HUMAN_REQUIRED"


def pending_documents(required_types: Iterable[str], present: Iterable[DocumentRecord]) -> tuple[str, ...]:
    required = set(required_types)
    present_types = {d.document_type for d in present}
    return tuple(sorted(required - present_types))


def document_quality(doc: DocumentRecord, required_fields: Iterable[str]) -> str:
    doc.validate()
    if doc.confidence < .8:
        return "HUMAN_REQUIRED"
    return "GREEN" if set(required_fields).issubset(dict(doc.fields)) else "RED"


def antifraud_signals(docs: Iterable[DocumentRecord]) -> tuple[str, ...]:
    seen_hash: dict[str, str] = {}
    signals: list[str] = []
    for doc in docs:
        doc.validate()
        previous = seen_hash.get(doc.content_hash)
        if previous and previous != doc.document_id:
            signals.append(f"DUPLICATE_CONTENT:{previous}:{doc.document_id}")
        seen_hash[doc.content_hash] = doc.document_id
    return tuple(sorted(signals))


# KYC-001
@dataclass(frozen=True)
class IdentityCheck:
    company_id: str
    person_id: str
    declared_name: str
    document_name: str
    declared_identifier: str
    document_identifier: str
    confidence: float

    def decision(self) -> tuple[str, str | None]:
        if not all((self.company_id.strip(), self.person_id.strip(), self.declared_name.strip(), self.document_name.strip(), self.declared_identifier.strip(), self.document_identifier.strip())):
            return "RED", None
        if self.confidence < .8:
            return "HUMAN_REQUIRED", "LOW_CONFIDENCE"
        if self.declared_name.casefold().strip() != self.document_name.casefold().strip() or self.declared_identifier.strip() != self.document_identifier.strip():
            return "HUMAN_REQUIRED", "HIGH_RISK"
        return "GREEN", None


# AML-001 -- signals/checklist only; never infers crime
@dataclass(frozen=True)
class AmlAssessment:
    checklist_complete: bool
    source_of_funds_supported: bool
    unexplained_inconsistencies: bool
    evidence_ref: str

    def decision(self) -> tuple[str, str | None]:
        if not self.evidence_ref.strip() or not self.checklist_complete:
            return "RED", None
        if not self.source_of_funds_supported or self.unexplained_inconsistencies:
            return "HUMAN_REQUIRED", "LEGAL_REQUIRED"
        return "GREEN", None


# BNK-001
@dataclass(frozen=True)
class BankCriterion:
    bank_id: str
    criterion: str
    value: str
    source_ref: str
    observed_at: str
    confidence: float
    case_count: int = 0

    def validate(self) -> None:
        if not all((self.bank_id.strip(), self.criterion.strip(), self.value.strip(), self.source_ref.strip(), self.observed_at.strip())):
            raise ValueError("bank criterion identity/provenance required")
        datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        if not 0 <= self.confidence <= 1 or self.case_count < 0:
            raise ValueError("invalid bank criterion confidence/cases")


# BNK-002
@dataclass(frozen=True)
class BankOption:
    bank_id: str
    approval_fit: float
    price_score: float
    speed_score: float
    evidence_ref: str


def rank_banks(options: Iterable[BankOption], weights: Mapping[str, float]) -> tuple[str, ...]:
    required = {"approval_fit", "price_score", "speed_score"}
    if set(weights) != required:
        raise ValueError("bank ranking weights must be explicit")
    rows = []
    for o in options:
        if not o.bank_id.strip() or not o.evidence_ref.strip():
            raise ValueError("bank option identity/evidence required")
        score = o.approval_fit * weights["approval_fit"] + o.price_score * weights["price_score"] + o.speed_score * weights["speed_score"]
        rows.append((score, o.bank_id))
    return tuple(bank for _, bank in sorted(rows, key=lambda x: (-x[0], x[1])))


# BNK-003
@dataclass(frozen=True)
class RoutingDecision:
    current_bank: str
    reason: str
    subsanable: bool
    attempts: int
    max_attempts: int
    alternatives: tuple[str, ...]

    def next_action(self) -> tuple[str, str | None]:
        if self.attempts >= self.max_attempts:
            return "HUMAN_REQUIRED", "HIGH_RISK"
        if self.subsanable:
            return "RETRY", self.current_bank
        return ("ROUTE_NEXT", self.alternatives[0]) if self.alternatives else ("HUMAN_REQUIRED", "LOW_CONFIDENCE")


# BNK-004
@dataclass(frozen=True)
class BankDossier:
    bank_id: str
    document_refs: tuple[str, ...]
    naming_standard: str
    cover_message_ref: str

    @property
    def ready(self) -> bool:
        return bool(self.bank_id.strip() and self.document_refs and all(x.strip() for x in self.document_refs) and self.naming_standard.strip() and self.cover_message_ref.strip())


# BNK-005
@dataclass(frozen=True)
class BankFollowUp:
    bank_id: str
    last_contact_at: str
    sla_hours: int
    preferred_channel: str

    def due(self, now: datetime) -> bool:
        if self.sla_hours <= 0:
            raise ValueError("sla_hours must be positive")
        last = datetime.fromisoformat(self.last_contact_at.replace("Z", "+00:00"))
        if last.tzinfo is None: last = last.replace(tzinfo=timezone.utc)
        return (now - last).total_seconds() >= self.sla_hours * 3600


# BNK-006
@dataclass(frozen=True)
class NegotiationProposal:
    requested_improvement: float
    authorized_limit: float
    evidence_ref: str

    def decision(self) -> tuple[str, str | None]:
        if not self.evidence_ref.strip(): return "RED", None
        if abs(self.requested_improvement) > abs(self.authorized_limit):
            return "HUMAN_REQUIRED", "HIGH_RISK"
        return "GREEN", None


# OFR-001
@dataclass(frozen=True)
class MortgageOffer:
    offer_id: str
    total_cost_eur: Decimal
    rate: Decimal
    fees_eur: Decimal
    evidence_ref: str


def compare_offers(offers: Iterable[MortgageOffer]) -> tuple[str, ...]:
    rows = tuple(offers)
    if not rows: raise ValueError("at least one offer required")
    if any(not o.offer_id.strip() or not o.evidence_ref.strip() for o in rows): raise ValueError("offer evidence required")
    return tuple(o.offer_id for o in sorted(rows, key=lambda o: (o.total_cost_eur, o.rate, o.fees_eur, o.offer_id)))


# REC-001
def final_recommendation(ranked_offer_ids: tuple[str, ...], confidence: float, rationale_refs: tuple[str, ...]) -> tuple[str, str | None]:
    if not ranked_offer_ids or not rationale_refs: return "RED", None
    if confidence < .8: return "HUMAN_REQUIRED", "LOW_CONFIDENCE"
    return "GREEN", ranked_offer_ids[0]


# TAS-001
@dataclass(frozen=True)
class ValuationEstimate:
    estimate_eur: Decimal
    confidence: float
    dispersion_pct: float
    evidence_refs: tuple[str, ...]

    def status(self, max_dispersion_pct: float) -> str:
        if not self.evidence_refs or self.confidence < .8: return "HUMAN_REQUIRED"
        return "GREEN" if self.dispersion_pct <= max_dispersion_pct else "BLOCKED"


# PROP-001
@dataclass(frozen=True)
class PropertyRisk:
    legal_signal: bool
    registry_conflict: bool
    cadastral_conflict: bool
    evidence_refs: tuple[str, ...]

    def decision(self) -> tuple[str, str | None]:
        if not self.evidence_refs: return "RED", None
        if self.legal_signal: return "HUMAN_REQUIRED", "LEGAL_REQUIRED"
        if self.registry_conflict or self.cadastral_conflict: return "HUMAN_REQUIRED", "HIGH_RISK"
        return "GREEN", None


# REGP-001
@dataclass(frozen=True)
class RegistryExtract:
    holder: str
    charges: tuple[str, ...]
    mortgages: tuple[str, ...]
    seizures: tuple[str, ...]
    source_ref: str
    confidence: float

    def status(self) -> str:
        if not self.source_ref.strip() or self.confidence < .8: return "HUMAN_REQUIRED"
        return "GREEN"


# CAT-001
@dataclass(frozen=True)
class CadastralExtract:
    reference: str
    area_m2: float
    use: str
    parcel: str
    source_ref: str

    def validate(self) -> None:
        if not all((self.reference.strip(), self.use.strip(), self.parcel.strip(), self.source_ref.strip())) or self.area_m2 <= 0:
            raise ValueError("invalid cadastral extract")


def registry_cadastre_coherent(registry_area: float, cadastral_area: float, tolerance_pct: float) -> bool:
    if registry_area <= 0 or cadastral_area <= 0 or tolerance_pct < 0: raise ValueError("invalid coherence inputs")
    return abs(registry_area - cadastral_area) / max(registry_area, cadastral_area) * 100 <= tolerance_pct


# NOT-001
@dataclass(frozen=True)
class NotaryReadiness:
    fein_ready: bool
    act_ready: bool
    payment_ready: bool
    agenda_ready: bool
    mandatory_human_signature: bool

    def decision(self) -> tuple[str, str | None]:
        if self.mandatory_human_signature: return "HUMAN_REQUIRED", "SIGNATURE_REQUIRED"
        return ("GREEN", None) if all((self.fein_ready, self.act_ready, self.payment_ready, self.agenda_ready)) else ("RED", None)


# PAY-001
def closing_balance(expected: Decimal, components: Iterable[Decimal]) -> tuple[str, Decimal]:
    actual = sum(components, Decimal("0")); diff = actual - expected
    return ("GREEN" if diff == 0 else "BLOCKED", diff)


# SLA-001
@dataclass(frozen=True)
class SlaCase:
    due_at: str
    completed_at: str | None = None

    def status(self, now: datetime) -> str:
        due = datetime.fromisoformat(self.due_at.replace("Z", "+00:00"))
        if self.completed_at:
            done = datetime.fromisoformat(self.completed_at.replace("Z", "+00:00")); return "GREEN" if done <= due else "RED"
        return "RED" if now > due else "GREEN"


# BLK-001
@dataclass(frozen=True)
class Blocker:
    blocker_id: str
    severity: str
    resolvable_automatically: bool
    human_reason: str | None = None

    def action(self) -> str:
        if self.resolvable_automatically: return "AUTO_RESOLVE"
        if self.human_reason in {"LEGAL_REQUIRED","SIGNATURE_REQUIRED","LOW_CONFIDENCE","HIGH_RISK","POLICY_CONFLICT","SECURITY_INCIDENT","MONEY_LIMIT","CUSTOMER_HUMAN_REQUEST"}: return "HUMAN_REQUIRED"
        return "BLOCKED"


# NBA-001
@dataclass(frozen=True)
class ActionCandidate:
    action: str
    benefit: float
    urgency: float
    risk: float


def next_best_action(candidates: Iterable[ActionCandidate]) -> str:
    rows = tuple(candidates)
    if not rows: raise ValueError("candidate required")
    return max(rows, key=lambda x: (x.benefit + x.urgency - x.risk, x.action)).action


# AGD-001
@dataclass(frozen=True)
class CalendarSlot:
    start: str
    end: str


def first_free_slot(candidates: Iterable[CalendarSlot], busy: Iterable[CalendarSlot]) -> CalendarSlot | None:
    busy_rows = tuple(busy)
    for slot in candidates:
        s1, e1 = datetime.fromisoformat(slot.start), datetime.fromisoformat(slot.end)
        if e1 <= s1: raise ValueError("invalid candidate slot")
        conflict = False
        for b in busy_rows:
            s2, e2 = datetime.fromisoformat(b.start), datetime.fromisoformat(b.end)
            if s1 < e2 and s2 < e1: conflict = True; break
        if not conflict: return slot
    return None


# 3RD-001
@dataclass(frozen=True)
class ThirdPartyTask:
    party_id: str
    task_id: str
    due_at: str
    evidence_ref: str
    completed: bool = False

    def status(self, now: datetime) -> str:
        if not all((self.party_id.strip(), self.task_id.strip(), self.evidence_ref.strip())): return "RED"
        if self.completed: return "GREEN"
        due = datetime.fromisoformat(self.due_at.replace("Z", "+00:00"))
        return "RED" if now > due else "GREEN"
