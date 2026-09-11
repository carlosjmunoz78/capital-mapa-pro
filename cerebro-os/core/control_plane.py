from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
import re
from typing import Iterable


HUMAN_REASONS = {
    "LEGAL_REQUIRED", "SIGNATURE_REQUIRED", "LOW_CONFIDENCE", "HIGH_RISK",
    "POLICY_CONFLICT", "SECURITY_INCIDENT", "MONEY_LIMIT", "CUSTOMER_HUMAN_REQUEST",
}
ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
SECRET_HINTS = {"password", "secret", "token", "private_key", "api_key"}


# CORE-001
@dataclass(frozen=True)
class CoreValue:
    company_id: str
    key: str
    value: str
    version: str
    provenance_ref: str


class CoreState:
    def __init__(self) -> None:
        self._values: dict[tuple[str, str], CoreValue] = {}

    def put(self, item: CoreValue) -> None:
        if not all((item.company_id.strip(), item.key.strip(), item.version.strip(), item.provenance_ref.strip())):
            raise ValueError("core value scope, key, version and provenance are required")
        self._values[(item.company_id, item.key)] = item

    def get(self, company_id: str, key: str) -> CoreValue | None:
        if not company_id.strip():
            raise ValueError("company_id required")
        return self._values.get((company_id, key))


# ORCH-001
@dataclass(frozen=True)
class OrchestratedTask:
    task_id: str
    company_id: str
    priority: int
    dependencies: tuple[str, ...] = ()
    max_attempts: int = 3


class Orchestrator:
    def __init__(self, company_id: str) -> None:
        if not company_id.strip():
            raise ValueError("company_id required")
        self.company_id = company_id
        self._tasks: dict[str, OrchestratedTask] = {}
        self._completed: set[str] = set()
        self._attempts: dict[str, int] = {}
        self._evidence: dict[str, str] = {}

    def add(self, task: OrchestratedTask) -> None:
        if task.company_id != self.company_id:
            raise ValueError("cross-company task denied")
        if not task.task_id.strip() or task.max_attempts < 1:
            raise ValueError("invalid task")
        if task.task_id in self._tasks:
            raise ValueError("duplicate task_id")
        if task.task_id in task.dependencies:
            raise ValueError("self dependency denied")
        self._tasks[task.task_id] = task

    def ready(self) -> tuple[str, ...]:
        heap: list[tuple[int, str]] = []
        for task_id, task in self._tasks.items():
            if task_id in self._completed:
                continue
            if self._attempts.get(task_id, 0) >= task.max_attempts:
                continue
            if all(dep in self._completed for dep in task.dependencies):
                heappush(heap, (-task.priority, task_id))
        result: list[str] = []
        while heap:
            _, task_id = heappop(heap)
            result.append(task_id)
        return tuple(result)

    def attempt(self, task_id: str, success: bool, evidence_ref: str | None = None) -> None:
        if task_id not in self._tasks:
            raise ValueError("unknown task")
        task = self._tasks[task_id]
        if not all(dep in self._completed for dep in task.dependencies):
            raise ValueError("dependencies not complete")
        self._attempts[task_id] = self._attempts.get(task_id, 0) + 1
        if success:
            if not (evidence_ref and evidence_ref.strip()):
                raise ValueError("successful task completion requires evidence_ref")
            self._evidence[task_id] = evidence_ref.strip()
            self._completed.add(task_id)

    def completion_evidence(self, task_id: str) -> str | None:
        if task_id not in self._tasks:
            raise ValueError("unknown task")
        return self._evidence.get(task_id)


# HEX-001
@dataclass(frozen=True)
class HumanException:
    company_id: str
    engine_id: str
    reason: str
    evidence_ref: str
    priority: int = 50


class HumanExceptionQueue:
    def __init__(self, company_id: str) -> None:
        self.company_id = company_id
        self._items: list[HumanException] = []

    def emit(self, item: HumanException) -> None:
        if item.company_id != self.company_id:
            raise ValueError("cross-company exception denied")
        if item.reason not in HUMAN_REASONS:
            raise ValueError("non-canonical human reason")
        if not item.engine_id.strip() or not item.evidence_ref.strip():
            raise ValueError("engine_id and evidence_ref required")
        self._items.append(item)

    def pending(self) -> tuple[HumanException, ...]:
        return tuple(sorted(self._items, key=lambda x: (-x.priority, x.engine_id, x.reason)))


# DEC-001
@dataclass(frozen=True)
class DecisionOption:
    option_id: str
    benefit: float
    cost: float
    urgency: float
    risk: float
    speed: float


@dataclass(frozen=True)
class DecisionResult:
    option_id: str
    score: float
    explanation: tuple[str, ...]


def rank_options(options: Iterable[DecisionOption], weights: dict[str, float]) -> tuple[DecisionResult, ...]:
    required = {"benefit", "cost", "urgency", "risk", "speed"}
    if set(weights) != required:
        raise ValueError("exact decision weights required")
    results: list[DecisionResult] = []
    for o in options:
        if not o.option_id.strip():
            raise ValueError("option_id required")
        score = (
            o.benefit * weights["benefit"]
            - o.cost * weights["cost"]
            + o.urgency * weights["urgency"]
            - o.risk * weights["risk"]
            + o.speed * weights["speed"]
        )
        results.append(DecisionResult(o.option_id, round(score, 6), (
            f"benefit={o.benefit}", f"cost={o.cost}", f"urgency={o.urgency}",
            f"risk={o.risk}", f"speed={o.speed}",
        )))
    return tuple(sorted(results, key=lambda x: (-x.score, x.option_id)))


# SEM-001
@dataclass(frozen=True)
class SemanticEntity:
    name: str
    fields: tuple[str, ...]


class SemanticCatalog:
    def __init__(self) -> None:
        self._entities: dict[str, SemanticEntity] = {}

    def register(self, entity: SemanticEntity) -> None:
        name = entity.name.strip().casefold()
        if not name or not entity.fields or len(entity.fields) != len(set(entity.fields)):
            raise ValueError("invalid semantic entity")
        if name in self._entities:
            raise ValueError("duplicate semantic entity")
        self._entities[name] = entity

    def resolve(self, name: str) -> SemanticEntity | None:
        return self._entities.get(name.strip().casefold())


# OWN-001
@dataclass(frozen=True)
class Ownership:
    engine_id: str
    owner: str
    approver: str
    backup_owner: str


class OwnershipRegistry:
    def __init__(self) -> None:
        self._items: dict[str, Ownership] = {}

    def set(self, item: Ownership) -> None:
        if not all((item.engine_id.strip(), item.owner.strip(), item.approver.strip(), item.backup_owner.strip())):
            raise ValueError("complete ownership required")
        self._items[item.engine_id] = item

    def get(self, engine_id: str) -> Ownership | None:
        return self._items.get(engine_id)


# OBJ-001
@dataclass(frozen=True)
class Objective:
    objective_id: str
    metric: str
    target: float
    actual: float
    direction: str = "AT_LEAST"

    def status(self) -> str:
        if self.direction == "AT_LEAST":
            return "GREEN" if self.actual >= self.target else "RED"
        if self.direction == "AT_MOST":
            return "GREEN" if self.actual <= self.target else "RED"
        raise ValueError("invalid objective direction")


# ADR-001
@dataclass(frozen=True)
class ArchitectureDecision:
    adr_id: str
    context: str
    choice: str
    alternatives: tuple[str, ...]
    consequences: str
    rollback: str


class ADRLog:
    def __init__(self) -> None:
        self._items: list[ArchitectureDecision] = []

    def append(self, item: ArchitectureDecision) -> None:
        if not all((item.adr_id.strip(), item.context.strip(), item.choice.strip(), item.consequences.strip(), item.rollback.strip())):
            raise ValueError("ADR fields required")
        if any(x.adr_id == item.adr_id for x in self._items):
            raise ValueError("ADR is append-only and ids are unique")
        self._items.append(item)

    def entries(self) -> tuple[ArchitectureDecision, ...]:
        return tuple(self._items)


# CFG-001
@dataclass(frozen=True)
class ConfigValue:
    key: str
    value: str
    environment: str
    version: str


class MasterConfig:
    def __init__(self) -> None:
        self._values: dict[tuple[str, str], ConfigValue] = {}

    def set(self, item: ConfigValue) -> None:
        lower = item.key.casefold()
        if item.environment not in ENVIRONMENTS or not item.version.strip() or not item.key.strip():
            raise ValueError("invalid config")
        if any(hint in lower for hint in SECRET_HINTS):
            raise ValueError("secrets must not be stored in master config")
        self._values[(item.environment, item.key)] = item

    def get(self, environment: str, key: str) -> ConfigValue | None:
        return self._values.get((environment, key))


# VER-001
def parse_semver(version: str) -> tuple[int, int, int]:
    match = SEMVER_RE.fullmatch(version)
    if not match:
        raise ValueError("invalid semver")
    return tuple(int(x) for x in match.groups())


def compatible(provider_version: str, required_version: str) -> bool:
    provider = parse_semver(provider_version)
    required = parse_semver(required_version)
    if provider[0] != required[0]:
        return False
    return provider >= required
