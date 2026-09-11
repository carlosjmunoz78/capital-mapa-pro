from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping


# MKT-001
@dataclass(frozen=True)
class CampaignExperiment:
    company_id: str
    campaign_id: str
    spend_eur: float
    budget_limit_eur: float
    leads: int
    conversions: int
    revenue_eur: float
    evidence_ref: str

    def validate(self) -> None:
        if not all((self.company_id.strip(), self.campaign_id.strip(), self.evidence_ref.strip())):
            raise ValueError("campaign identity and evidence required")
        if min(self.spend_eur, self.budget_limit_eur, self.leads, self.conversions, self.revenue_eur) < 0:
            raise ValueError("campaign metrics cannot be negative")
        if self.conversions > self.leads:
            raise ValueError("conversions cannot exceed leads")

    @property
    def decision(self) -> str:
        self.validate()
        return "HUMAN_REQUIRED" if self.spend_eur > self.budget_limit_eur else "GREEN"

    @property
    def roi(self) -> float:
        self.validate()
        return 0.0 if self.spend_eur == 0 else round((self.revenue_eur - self.spend_eur) / self.spend_eur, 6)


# SEO-001
@dataclass(frozen=True)
class SeoFinding:
    finding_id: str
    impact: int
    effort: int
    evidence_ref: str


def seo_backlog(findings: Iterable[SeoFinding]) -> tuple[str, ...]:
    rows = []
    for f in findings:
        if not f.finding_id.strip() or not f.evidence_ref.strip() or f.impact < 0 or f.effort < 0:
            raise ValueError("invalid SEO finding")
        score = f.impact / max(1, f.effort)
        rows.append((score, f.impact, f.finding_id))
    return tuple(x[2] for x in sorted(rows, key=lambda x: (-x[0], -x[1], x[2])))


def seo_publish_gate(*, qa_green: bool, source_evidence: bool, rollback_ref: str) -> str:
    return "GREEN" if qa_green and source_evidence and rollback_ref.strip() else "BLOCKED"


# CAP-001
@dataclass(frozen=True)
class AcquisitionChannel:
    channel: str
    cost_eur: float
    budget_limit_eur: float
    leads: int
    qualified_leads: int

    @property
    def efficiency(self) -> float:
        return self.qualified_leads / max(self.cost_eur, 1.0)


def choose_acquisition_channel(channels: Iterable[AcquisitionChannel]) -> tuple[str, str]:
    rows = tuple(channels)
    if not rows:
        raise ValueError("at least one channel required")
    if any(x.cost_eur > x.budget_limit_eur for x in rows):
        return "HUMAN_REQUIRED", "MONEY_LIMIT"
    best = max(rows, key=lambda x: (x.efficiency, x.qualified_leads, x.channel))
    return "GREEN", best.channel


# LEAD-001
@dataclass(frozen=True)
class LeadScore:
    score: float
    explanation: tuple[str, ...]


def score_lead(features: Mapping[str, float], weights: Mapping[str, float]) -> LeadScore:
    if set(features) != set(weights) or not features:
        raise ValueError("features and weights must match and be non-empty")
    parts = tuple(sorted((name, float(features[name]), float(weights[name])) for name in features))
    score = sum(value * weight for _, value, weight in parts)
    return LeadScore(round(score, 6), tuple(f"{name}={value}*{weight}" for name, value, weight in parts))


# SALE-001
SALES_NEXT = {
    "NEW": "QUALIFY",
    "QUALIFIED": "CONTACT",
    "CONTACTED": "FOLLOW_UP",
    "PROPOSAL": "NEGOTIATE",
    "WON": "POST_SALE",
    "LOST": "LEARN",
}

def sales_next_action(stage: str) -> str:
    if stage not in SALES_NEXT:
        raise ValueError("unknown sales stage")
    return SALES_NEXT[stage]


# COM-001
@dataclass(frozen=True)
class CommunicationRequest:
    company_id: str
    channel: str
    consent: bool
    low_risk: bool
    evidence_ref: str

    def decision(self) -> str:
        if not self.company_id.strip() or not self.evidence_ref.strip():
            return "RED"
        if not self.consent:
            return "BLOCKED"
        if not self.low_risk:
            return "HUMAN_REQUIRED"
        if self.channel not in {"EMAIL", "SMS", "WHATSAPP", "IN_APP", "VOICE"}:
            raise ValueError("unsupported channel")
        return "GREEN"


# NOTIF-001
@dataclass(frozen=True)
class Notification:
    key: str
    priority: int
    summary: str


def notification_digest(items: Iterable[Notification], limit: int = 10) -> tuple[Notification, ...]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    dedup: dict[str, Notification] = {}
    for item in items:
        if not item.key.strip() or not item.summary.strip():
            raise ValueError("notification key/summary required")
        current = dedup.get(item.key)
        if current is None or item.priority > current.priority:
            dedup[item.key] = item
    return tuple(sorted(dedup.values(), key=lambda x: (-x.priority, x.key))[:limit])


# VOICE-001
@dataclass(frozen=True)
class VoiceSession:
    company_id: str
    session_id: str
    consent: bool
    transcript_ref: str
    cost_eur: float = 0.0
    approved_limit_eur: float = 0.0

    def decision(self) -> tuple[str, str | None]:
        if not all((self.company_id.strip(), self.session_id.strip(), self.transcript_ref.strip())):
            return "RED", None
        if not self.consent:
            return "HUMAN_REQUIRED", "LEGAL_REQUIRED"
        if self.cost_eur > self.approved_limit_eur:
            return "HUMAN_REQUIRED", "MONEY_LIMIT"
        return "GREEN", None


# C360-001
@dataclass(frozen=True)
class CustomerReference:
    system: str
    record_ref: str


def customer_360(customer_id: str, refs: Iterable[CustomerReference]) -> dict:
    if not customer_id.strip():
        raise ValueError("customer_id required")
    rows = tuple(refs)
    if any(not r.system.strip() or not r.record_ref.strip() for r in rows):
        raise ValueError("system/reference required")
    return {"customer_id": customer_id, "references": tuple(sorted((r.system, r.record_ref) for r in rows))}


# CX-001
def cx_friction(signals: Mapping[str, float], weights: Mapping[str, float]) -> float:
    if set(signals) != set(weights) or not signals:
        raise ValueError("signals and weights must match")
    if any(not 0 <= float(v) <= 1 for v in signals.values()):
        raise ValueError("CX signals must be normalized")
    total = sum(abs(float(w)) for w in weights.values())
    return 0.0 if total == 0 else round(sum(float(signals[k]) * float(weights[k]) for k in signals) / total, 6)


# RET-001
@dataclass(frozen=True)
class RetentionDecision:
    risk_score: float
    threshold: float
    action: str
    cost_eur: float = 0.0
    approved_limit_eur: float = 0.0

    def decision(self) -> tuple[str, str]:
        if not 0 <= self.risk_score <= 1 or not 0 <= self.threshold <= 1:
            raise ValueError("risk/threshold must be normalized")
        if self.cost_eur > self.approved_limit_eur:
            return "HUMAN_REQUIRED", "MONEY_LIMIT"
        return ("GREEN", self.action) if self.risk_score >= self.threshold else ("GREEN", "NO_ACTION")


# POST-001
POST_STEPS = ("CLOSE", "FOLLOW_UP", "REVIEW", "REFERRAL", "REFINANCE_WATCH")
class PostSaleFlow:
    def __init__(self) -> None:
        self._done: set[str] = set()
        self._evidence: dict[str, str] = {}

    def complete(self, step: str, evidence_ref: str | None = None) -> None:
        if step not in POST_STEPS:
            raise ValueError("unknown post-sale step")
        idx = POST_STEPS.index(step)
        if any(previous not in self._done for previous in POST_STEPS[:idx]):
            raise ValueError("post-sale dependency incomplete")
        if not evidence_ref or not evidence_ref.strip():
            raise ValueError("post-sale completion requires evidence_ref")
        self._evidence[step] = evidence_ref.strip()
        self._done.add(step)

    def evidence(self, step: str) -> str | None:
        if step not in POST_STEPS:
            raise ValueError("unknown post-sale step")
        return self._evidence.get(step)

    def next_step(self) -> str | None:
        return next((s for s in POST_STEPS if s not in self._done), None)


# REF-001
def referral_eligibility(*, satisfaction: float, successful_outcome: bool, min_satisfaction: float) -> str:
    if not 0 <= satisfaction <= 1 or not 0 <= min_satisfaction <= 1:
        raise ValueError("satisfaction values must be normalized")
    return "GREEN" if successful_outcome and satisfaction >= min_satisfaction else "NO_ACTION"


# REP-001
@dataclass(frozen=True)
class Review:
    rating: float
    text: str
    evidence_ref: str

    def triage(self) -> tuple[str, str]:
        if not 0 <= self.rating <= 5 or not self.evidence_ref.strip():
            raise ValueError("invalid review")
        if self.rating <= 2:
            return "HUMAN_REQUIRED", "HIGH_RISK"
        return "GREEN", "LOW_RISK_RESPONSE_CANDIDATE"


# CMP-001
@dataclass(frozen=True)
class Complaint:
    complaint_id: str
    severity: str
    legal_signal: bool
    evidence_ref: str

    def decision(self) -> tuple[str, str | None]:
        if not self.complaint_id.strip() or not self.evidence_ref.strip():
            return "RED", None
        if self.legal_signal:
            return "HUMAN_REQUIRED", "LEGAL_REQUIRED"
        if self.severity in {"HIGH", "CRITICAL"}:
            return "HUMAN_REQUIRED", "HIGH_RISK"
        if self.severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            raise ValueError("invalid complaint severity")
        return "GREEN", None


# COMPET-001
@dataclass(frozen=True)
class CompetitorSnapshot:
    competitor_id: str
    observed_at: str
    source_ref: str
    confidence: float
    facts: tuple[tuple[str, str], ...]

    def validate(self) -> None:
        if not all((self.competitor_id.strip(), self.observed_at.strip(), self.source_ref.strip())):
            raise ValueError("competitor identity/evidence required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be normalized")
        datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))

    def status(self, min_confidence: float = 0.75) -> str:
        self.validate()
        return "GREEN" if self.confidence >= min_confidence else "HUMAN_REQUIRED"


def competitor_diff(old: CompetitorSnapshot, new: CompetitorSnapshot) -> tuple[tuple[str, str | None, str | None], ...]:
    old.validate(); new.validate()
    if old.competitor_id != new.competitor_id:
        raise ValueError("competitor mismatch")
    a, b = dict(old.facts), dict(new.facts)
    keys = sorted(set(a) | set(b))
    return tuple((key, a.get(key), b.get(key)) for key in keys if a.get(key) != b.get(key))
