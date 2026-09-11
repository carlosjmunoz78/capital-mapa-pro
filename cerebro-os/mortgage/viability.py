from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


OPS = {"<", "<=", ">", ">=", "=="}


@dataclass(frozen=True)
class ViabilityRule:
    rule_id: str
    field: str
    operator: str
    threshold: float
    weight: float
    critical: bool
    version: str
    explanation: str

    def validate(self) -> None:
        if not all((self.rule_id.strip(), self.field.strip(), self.version.strip(), self.explanation.strip())):
            raise ValueError("rule_id, field, version and explanation are required")
        if self.operator not in OPS:
            raise ValueError("unsupported operator")
        if self.weight < 0:
            raise ValueError("weight must be >= 0")


@dataclass(frozen=True)
class ViabilityResult:
    status: str
    score: float
    confidence: float
    passed_rules: tuple[str, ...]
    failed_rules: tuple[str, ...]
    missing_fields: tuple[str, ...]
    explanations: tuple[str, ...]
    rules_version: str


class ViabilityEvaluator:
    """Versioned deterministic rule evaluator for VIA-001.

    No underwriting thresholds are embedded here. Rules must be supplied by the
    authorized business knowledge/policy source. The evaluator only applies the
    supplied versioned rules and emits confidence/explanations.
    """

    def __init__(self, company_id: str, rules: tuple[ViabilityRule, ...], min_confidence: float = 0.8) -> None:
        if not company_id.strip():
            raise ValueError("company_id required")
        if not rules:
            raise ValueError("at least one rule required")
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")
        for rule in rules:
            rule.validate()
        versions = {r.version for r in rules}
        if len(versions) != 1:
            raise ValueError("all rules in one evaluation must share version")
        if len({r.rule_id for r in rules}) != len(rules):
            raise ValueError("rule_id must be unique")
        self.company_id = company_id
        self.rules = rules
        self.min_confidence = min_confidence
        self.rules_version = next(iter(versions))

    @staticmethod
    def _passes(value: float, operator: str, threshold: float) -> bool:
        if operator == "<":
            return value < threshold
        if operator == "<=":
            return value <= threshold
        if operator == ">":
            return value > threshold
        if operator == ">=":
            return value >= threshold
        return value == threshold

    def evaluate(self, company_id: str, inputs: Mapping[str, float]) -> ViabilityResult:
        if company_id != self.company_id:
            raise ValueError("cross-company viability evaluation denied")

        passed: list[str] = []
        failed: list[str] = []
        missing: list[str] = []
        explanations: list[str] = []
        total_weight = sum(r.weight for r in self.rules)
        passed_weight = 0.0
        evaluated_weight = 0.0
        critical_failed = False

        for rule in self.rules:
            if rule.field not in inputs:
                missing.append(rule.field)
                explanations.append(f"{rule.rule_id}: missing {rule.field}")
                continue
            value = float(inputs[rule.field])
            evaluated_weight += rule.weight
            ok = self._passes(value, rule.operator, rule.threshold)
            explanations.append(rule.explanation)
            if ok:
                passed.append(rule.rule_id)
                passed_weight += rule.weight
            else:
                failed.append(rule.rule_id)
                critical_failed = critical_failed or rule.critical

        score = 0.0 if total_weight == 0 else passed_weight / total_weight
        confidence = 0.0 if total_weight == 0 else evaluated_weight / total_weight

        if missing or confidence < self.min_confidence:
            status = "HUMAN_REQUIRED"
        elif critical_failed:
            status = "RED"
        else:
            status = "GREEN"

        return ViabilityResult(
            status=status,
            score=round(score, 6),
            confidence=round(confidence, 6),
            passed_rules=tuple(passed),
            failed_rules=tuple(failed),
            missing_fields=tuple(sorted(set(missing))),
            explanations=tuple(explanations),
            rules_version=self.rules_version,
        )
