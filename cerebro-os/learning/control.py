from __future__ import annotations

from dataclasses import dataclass
from collections import Counter

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


# LRN-001
@dataclass(frozen=True)
class OutcomeEvent:
    company_id: str
    domain: str
    action: str
    outcome: str
    evidence_ref: str
    sensitive: bool = False
    environment: str = "LAB"
    version: str = "1.0.0"

    def validate(self) -> None:
        if not all((self.company_id.strip(), self.domain.strip(), self.action.strip(), self.outcome.strip(), self.evidence_ref.strip(), self.version.strip())):
            raise ValueError("outcome event fields required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")


@dataclass(frozen=True)
class RuleCandidate:
    domain: str
    action: str
    outcome: str
    cases: int
    sensitive: bool
    status: str = "CANDIDATE_REVIEW"


class LearningEngine:
    def __init__(self, company_id: str, environment: str = "LAB", version: str = "1.0.0") -> None:
        if not company_id.strip() or not version.strip():
            raise ValueError("company_id and version required")
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        self.company_id = company_id
        self.environment = environment
        self.version = version
        self._events: list[OutcomeEvent] = []

    def record(self, event: OutcomeEvent) -> None:
        event.validate()
        if event.company_id != self.company_id:
            raise ValueError("cross-company learning event denied")
        if event.environment != self.environment or event.version != self.version:
            raise ValueError("cross-scope learning event denied")
        self._events.append(event)

    def candidates(self, min_cases: int = 3) -> tuple[RuleCandidate, ...]:
        if min_cases < 2:
            raise ValueError("min_cases must be >= 2")
        counts = Counter((e.domain, e.action, e.outcome, e.sensitive) for e in self._events)
        result = [RuleCandidate(d, a, o, count, sensitive) for (d, a, o, sensitive), count in counts.items() if count >= min_cases]
        return tuple(sorted(result, key=lambda x: (-x.cases, x.domain, x.action, x.outcome)))


# TRN-001
@dataclass(frozen=True)
class TrainingRun:
    run_id: str
    company_id: str
    engine_id: str
    dataset_version: str
    code_version: str
    environment: str
    metrics: tuple[tuple[str, float], ...]
    evidence_ref: str

    def validate(self) -> None:
        if not all((self.run_id.strip(), self.company_id.strip(), self.engine_id.strip(), self.dataset_version.strip(), self.code_version.strip(), self.evidence_ref.strip())):
            raise ValueError("training run identity and evidence required")
        if self.environment not in {"LAB", "PREPROD"}:
            raise ValueError("training runs cannot execute/promote directly in PROD")
        if len(dict(self.metrics)) != len(self.metrics):
            raise ValueError("duplicate metric names")


class TrainingRegistry:
    def __init__(self) -> None:
        self._runs: dict[str, TrainingRun] = {}
        self._champions: dict[tuple[str, str, str, str], str] = {}
        self._promotion_evidence: dict[str, dict[str, str]] = {}

    def register(self, run: TrainingRun) -> None:
        run.validate()
        if run.run_id in self._runs:
            raise ValueError("duplicate run_id")
        self._runs[run.run_id] = run

    def promote_champion(self, run_id: str, tribunal_approved: bool, reproducible: bool, evidence_refs: dict[str, str] | None = None) -> None:
        if run_id not in self._runs:
            raise ValueError("unknown run")
        if not tribunal_approved or not reproducible:
            raise ValueError("champion promotion requires tribunal and reproducibility")
        refs = evidence_refs or {}
        required = ("tribunal", "reproducibility")
        if any(not str(refs.get(name, "")).strip() for name in required):
            raise ValueError("champion promotion requires tribunal and reproducibility evidence")
        run = self._runs[run_id]
        key = (run.company_id, run.engine_id, run.environment, run.code_version)
        self._champions[key] = run_id
        self._promotion_evidence[run_id] = {name: str(refs[name]).strip() for name in required}

    def champion(self, company_id: str, engine_id: str, environment: str = "LAB", code_version: str = "git-1") -> TrainingRun | None:
        run_id = self._champions.get((company_id, engine_id, environment, code_version))
        return self._runs.get(run_id) if run_id else None

    def promotion_evidence(self, run_id: str) -> dict[str, str] | None:
        return self._promotion_evidence.get(run_id)


# RSH-001
@dataclass(frozen=True)
class ResearchSource:
    company_id: str
    source_ref: str
    content_ref: str
    confidence: float
    official: bool = False

    def validate(self) -> None:
        if not all((self.company_id.strip(), self.source_ref.strip(), self.content_ref.strip())):
            raise ValueError("research source identity required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class ResearchDossier:
    company_id: str
    topic: str
    sources: tuple[ResearchSource, ...]

    def validate(self) -> None:
        if not self.company_id.strip() or not self.topic.strip() or not self.sources:
            raise ValueError("research dossier requires company, topic and sources")
        for source in self.sources:
            source.validate()
            if source.company_id != self.company_id:
                raise ValueError("cross-company research source denied")

    def confidence(self) -> float:
        self.validate()
        return round(sum(s.confidence for s in self.sources) / len(self.sources), 6)

    def status(self, min_confidence: float = 0.75) -> str:
        confidence = self.confidence()
        if confidence < min_confidence:
            return "HUMAN_REQUIRED"
        return "GREEN" if any(s.official for s in self.sources) or len(self.sources) >= 2 else "DOCUMENTED_PARTIAL"

    def knowledge_write_allowed(self) -> bool:
        return False


# CON-001
@dataclass(frozen=True)
class ConversationExtraction:
    company_id: str
    conversation_ref: str
    facts: tuple[str, ...] = ()
    tasks: tuple[str, ...] = ()
    decisions: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    confidence: float = 1.0
    sensitive: bool = False

    def validate(self) -> None:
        if not self.company_id.strip() or not self.conversation_ref.strip():
            raise ValueError("conversation scope and reference required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not any((self.facts, self.tasks, self.decisions, self.risks)):
            raise ValueError("at least one structured extraction required")

    def status(self, min_confidence: float = 0.8) -> str:
        self.validate()
        if self.sensitive or self.confidence < min_confidence:
            return "HUMAN_REQUIRED"
        return "GREEN"
