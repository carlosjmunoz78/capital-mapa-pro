from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Mapping

# APP-001 / CRM-001: wrappers only; never mutate legacy contracts directly.
@dataclass(frozen=True)
class LegacyContract:
    system: str
    version: str
    read_refs: tuple[str, ...]
    write_refs: tuple[str, ...]
    snapshot_ref: str

    def validate(self) -> None:
        if self.system not in {"APP", "CRM"}:
            raise ValueError("unsupported legacy system")
        if not self.version.strip() or not self.snapshot_ref.strip():
            raise ValueError("version and snapshot required")

    def change_allowed(self, tests_green: bool, rollback_verified: bool, explicit_scope: bool) -> bool:
        self.validate()
        return tests_green and rollback_verified and explicit_scope


# ARCH-001
@dataclass(frozen=True)
class ArchitectureFinding:
    kind: str
    component: str
    evidence_ref: str
    severity: int


def architecture_score(findings: Iterable[ArchitectureFinding]) -> int:
    total = 0
    for f in findings:
        if f.kind not in {"DUPLICATION", "COUPLING", "DRIFT", "DEBT", "CONTRACT_VIOLATION"}:
            raise ValueError("unknown architecture finding")
        if not f.component.strip() or not f.evidence_ref.strip() or f.severity < 0:
            raise ValueError("invalid architecture finding")
        total += f.severity
    return total


# DEBT-001
@dataclass(frozen=True)
class DebtItem:
    debt_id: str
    impact: float
    risk: float
    fix_cost: float
    evidence_ref: str

    @property
    def priority(self) -> float:
        if not self.debt_id.strip() or not self.evidence_ref.strip() or self.fix_cost < 0:
            raise ValueError("invalid debt item")
        return round((self.impact + self.risk) / max(self.fix_cost, 1.0), 6)


# MIG-001
@dataclass(frozen=True)
class MigrationPlan:
    migration_id: str
    up_ref: str
    down_ref: str
    test_ref: str
    backup_ref: str
    rollback_tested: bool

    @property
    def green(self) -> bool:
        return all((self.migration_id.strip(), self.up_ref.strip(), self.down_ref.strip(), self.test_ref.strip(), self.backup_ref.strip(), self.rollback_tested))


# FF-001
@dataclass(frozen=True)
class FeatureFlag:
    flag: str
    environment: str
    percentage: int
    roles: frozenset[str]

    def enabled(self, subject_bucket: int, role: str) -> bool:
        if self.environment not in {"LAB", "PREPROD", "PROD"} or not 0 <= self.percentage <= 100 or not 0 <= subject_bucket < 100:
            raise ValueError("invalid feature flag")
        return subject_bucket < self.percentage and (not self.roles or role in self.roles)


# CAN-001
@dataclass(frozen=True)
class CanaryStage:
    percentage: int
    metric_value: float
    min_metric: float
    rollback_ref: str

    def decision(self) -> str:
        if self.percentage not in {10, 50, 100} or not self.rollback_ref.strip():
            return "BLOCKED"
        return "PROMOTE" if self.metric_value >= self.min_metric else "ROLLBACK"


# OPT-001
@dataclass(frozen=True)
class ResourceUsage:
    job_id: str
    duplicate: bool
    idle: bool
    bytes_reclaimable: int
    evidence_ref: str


def optimization_actions(rows: Iterable[ResourceUsage]) -> tuple[str, ...]:
    actions=[]
    for r in rows:
        if not r.job_id.strip() or not r.evidence_ref.strip() or r.bytes_reclaimable < 0:
            raise ValueError("invalid resource usage")
        if r.duplicate: actions.append(f"DEDUP:{r.job_id}")
        if r.idle: actions.append(f"STOP_IDLE:{r.job_id}")
        if r.bytes_reclaimable: actions.append(f"COMPACT:{r.job_id}:{r.bytes_reclaimable}")
    return tuple(sorted(actions))


# AUTO-001
@dataclass(frozen=True)
class AutomationCandidate:
    task: str
    repeats_per_month: int
    minutes_each: float
    implementation_hours: float
    risk: str

    @property
    def monthly_hours_saved(self) -> float:
        return self.repeats_per_month * self.minutes_each / 60

    def decision(self) -> str:
        if self.repeats_per_month < 0 or self.minutes_each < 0 or self.implementation_hours < 0:
            raise ValueError("invalid automation candidate")
        if self.risk == "HIGH": return "HUMAN_REQUIRED"
        return "PLAN" if self.monthly_hours_saved > self.implementation_hours else "NO_ACTION"


# DOCS-001
REQUIRED_DOCS=("engine_registry","contracts","dependency_map","runbook","changelog","backup","rebuild","autonomy")
def docs_gate(updated: Mapping[str,bool]) -> str:
    return "GREEN" if all(updated.get(x,False) for x in REQUIRED_DOCS) else "BLOCKED"


# WEB-001
@dataclass(frozen=True)
class WebChange:
    change_id: str
    backup_verified: bool
    tests_green: bool
    seo_check_green: bool
    rollback_ref: str
    environment: str

    def decision(self) -> str:
        if self.environment == "PROD": return "BLOCKED"
        return "GREEN" if self.backup_verified and self.tests_green and self.seo_check_green and self.rollback_ref.strip() else "RED"


# INT-001
@dataclass(frozen=True)
class IntegrationRecord:
    integration_id: str
    writers: tuple[str,...]
    readers: tuple[str,...]
    owner: str
    health: str
    credential_ref: str

    def validate(self) -> None:
        if not all((self.integration_id.strip(),self.owner.strip(),self.health.strip(),self.credential_ref.strip())):
            raise ValueError("integration metadata required")
        if "=" in self.credential_ref:
            raise ValueError("credential value cannot be embedded")


# Generic source snapshot utility used by DEP-001 evidence generation.
def manifest_digest(entries: Mapping[str, Iterable[str]]) -> str:
    canonical=tuple(sorted((k,tuple(sorted(v))) for k,v in entries.items()))
    return sha256(repr(canonical).encode()).hexdigest()
