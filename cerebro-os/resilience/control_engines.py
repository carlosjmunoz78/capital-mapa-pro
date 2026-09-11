from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Mapping


# SIM-001
@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    deltas: tuple[tuple[str, float], ...]


def simulate(baseline: Mapping[str, float], scenario: Scenario) -> dict[str, float]:
    if not scenario.scenario_id.strip():
        raise ValueError("scenario_id required")
    result = {k: float(v) for k, v in baseline.items()}
    for key, delta in scenario.deltas:
        result[key] = result.get(key, 0.0) + float(delta)
    return result


# TWIN-001
@dataclass(frozen=True)
class TwinSnapshot:
    company_id: str
    version: str
    state: tuple[tuple[str, str], ...]

    def validate(self) -> None:
        if not self.company_id.strip() or not self.version.strip():
            raise ValueError("company_id and version required")
        if len(dict(self.state)) != len(self.state):
            raise ValueError("duplicate twin state key")

    @property
    def digest(self) -> str:
        self.validate()
        payload = repr((self.company_id, self.version, tuple(sorted(self.state)))).encode("utf-8")
        return sha256(payload).hexdigest()


# INC-001
INCIDENT_STATES = {"OPEN", "MITIGATED", "RESOLVED"}
@dataclass(frozen=True)
class Incident:
    incident_id: str
    company_id: str
    category: str
    severity: str
    evidence_ref: str
    state: str = "OPEN"

    def validate(self) -> None:
        if not all((self.incident_id.strip(), self.company_id.strip(), self.category.strip(), self.evidence_ref.strip())):
            raise ValueError("incident identity and evidence required")
        if self.severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} or self.state not in INCIDENT_STATES:
            raise ValueError("invalid incident severity/state")

    @property
    def human_reason(self) -> str | None:
        if self.category == "SECURITY" and self.severity in {"HIGH", "CRITICAL"}:
            return "SECURITY_INCIDENT"
        if self.severity == "CRITICAL":
            return "HIGH_RISK"
        return None


# SELF-001
@dataclass(frozen=True)
class RepairAction:
    action_id: str
    reversible: bool
    precheck_green: bool
    postcheck_green: bool
    rollback_ref: str

    @property
    def allowed(self) -> bool:
        return bool(self.action_id.strip() and self.reversible and self.precheck_green and self.rollback_ref.strip())

    @property
    def result(self) -> str:
        if not self.allowed:
            return "BLOCKED"
        return "GREEN" if self.postcheck_green else "ROLLBACK_REQUIRED"


# SEC-001
@dataclass(frozen=True)
class SecurityRequest:
    company_id: str
    actor_scopes: frozenset[str]
    required_scopes: frozenset[str]
    high_risk: bool = False


def security_decision(req: SecurityRequest) -> str:
    if not req.company_id.strip():
        return "DENY"
    if not req.required_scopes.issubset(req.actor_scopes):
        return "DENY"
    if req.high_risk:
        return "HUMAN_REQUIRED"
    return "ALLOW"


# IAM-001
@dataclass(frozen=True)
class IdentityGrant:
    identity_id: str
    company_id: str
    engine_id: str
    permissions: frozenset[str]
    environment: str

    def validate(self) -> None:
        if not all((self.identity_id.strip(), self.company_id.strip(), self.engine_id.strip())):
            raise ValueError("identity scope required")
        if self.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("invalid environment")
        if not self.permissions:
            raise ValueError("least-privilege permission set required")

    def allows(self, permission: str, company_id: str, environment: str) -> bool:
        self.validate()
        return company_id == self.company_id and environment == self.environment and permission in self.permissions


# SEC-002
@dataclass(frozen=True)
class SecretReference:
    provider: str
    path: str

    def validate(self) -> None:
        if not self.provider.strip() or not self.path.strip():
            raise ValueError("secret provider/path required")
        lower = self.path.casefold()
        if any(marker in lower for marker in ("=", "bearer ", "password:", "secret_value")):
            raise ValueError("embedded secret value denied")


# RED-001
@dataclass(frozen=True)
class RedTeamCase:
    case_id: str
    expected_decision: str
    actual_decision: str
    evidence_ref: str

    @property
    def passed(self) -> bool:
        return bool(self.case_id.strip() and self.evidence_ref.strip() and self.expected_decision == self.actual_decision)


# QA-001
@dataclass(frozen=True)
class SoftwareQualityGate:
    unit: bool
    contract: bool
    integration: bool
    regression: bool
    evidence_ref: str

    @property
    def green(self) -> bool:
        return all((self.unit, self.contract, self.integration, self.regression, bool(self.evidence_ref.strip())))


# QAB-001
@dataclass(frozen=True)
class ProcessQualityGate:
    process_id: str
    required_checks: tuple[str, ...]
    passed_checks: frozenset[str]
    evidence_ref: str

    @property
    def green(self) -> bool:
        return bool(self.process_id.strip() and self.evidence_ref.strip() and set(self.required_checks).issubset(self.passed_checks))


# REG-001
@dataclass(frozen=True)
class RegressionBaseline:
    contract_hash: str
    behavior_hash: str


def regression_status(old: RegressionBaseline, new: RegressionBaseline, change_approved: bool = False) -> str:
    if old == new:
        return "GREEN"
    return "GREEN" if change_approved else "RED"


# BCP-001
@dataclass(frozen=True)
class ContinuityReadiness:
    backup_verified: bool
    restore_verified: bool
    rebuild_verified: bool
    alternate_runtime_ready: bool
    runbook_ref: str

    @property
    def green(self) -> bool:
        return all((self.backup_verified, self.restore_verified, self.rebuild_verified, self.alternate_runtime_ready, bool(self.runbook_ref.strip())))


# CRS-001
@dataclass(frozen=True)
class CrisisAssessment:
    company_id: str
    severity: str
    blast_radius: str
    evidence_ref: str

    def decision(self) -> tuple[str, str | None]:
        if not self.company_id.strip() or not self.evidence_ref.strip():
            return "RED", None
        if self.severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            raise ValueError("invalid severity")
        if self.severity in {"HIGH", "CRITICAL"}:
            return "HUMAN_REQUIRED", "HIGH_RISK"
        return "GREEN", None
