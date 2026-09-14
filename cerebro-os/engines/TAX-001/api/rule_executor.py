from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

ENGINE_ID = "TAX-001"
VERSION = "0.1.0"
ENVIRONMENT = "LAB"
REQUIRED_LOCK_ARTIFACTS = ("AW", "AV", "BH")
ALLOWED_OPERATIONS = {"CLASSIFY", "CALCULATE", "EXPLAIN", "CHECK_DEADLINE"}
ALLOWED_EXPRESSION_TYPES = {
    "IDENTITY_FACT",
    "MULTIPLY_FACT_BY_RATE",
    "ADD_FACTS",
    "COMPARE_GTE",
}


def _human(payload: dict[str, Any], code: str, reason: str, *, evidence_refs: list[str] | None = None) -> dict[str, Any]:
    return {
        "request_id": str(payload.get("request_id", "")),
        "company_id": str(payload.get("company_id", "")),
        "engine_id": ENGINE_ID,
        "version": VERSION,
        "environment": ENVIRONMENT,
        "status": "HUMAN_REQUIRED",
        "confidence": 0.0,
        "human_required": code,
        "reason": reason,
        "evidence_refs": evidence_refs or [],
        "cost_eur": 0.0,
    }


def _parse_date(value: Any, field: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return date.fromisoformat(value.strip())


def _decimal(value: Any, field: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field} must be numeric") from exc


def validate_corpus_lock(corpus_lock: dict[str, Any], artifact_hashes: dict[str, str]) -> tuple[bool, str]:
    if not isinstance(corpus_lock, dict) or corpus_lock.get("status") != "BOUND":
        return False, "Fiscal corpus lock is not BOUND."
    artifacts = corpus_lock.get("artifacts")
    if not isinstance(artifacts, dict):
        return False, "Fiscal corpus lock artifacts are missing."
    for artifact_id in REQUIRED_LOCK_ARTIFACTS:
        expected = artifacts.get(artifact_id, {}).get("sha256") if isinstance(artifacts.get(artifact_id), dict) else None
        actual = artifact_hashes.get(artifact_id) if isinstance(artifact_hashes, dict) else None
        if not isinstance(expected, str) or len(expected) != 64:
            return False, f"Corpus lock {artifact_id} does not contain a canonical SHA-256."
        if actual != expected:
            return False, f"Corpus artifact hash mismatch for {artifact_id}."
    return True, "Corpus lock verified."


def _execute_expression(expression: dict[str, Any], facts: dict[str, Any]) -> Any:
    expression_type = expression.get("type")
    if expression_type not in ALLOWED_EXPRESSION_TYPES:
        raise ValueError("expression type is not allow-listed")

    if expression_type == "IDENTITY_FACT":
        fact = expression.get("fact")
        if fact not in facts:
            raise KeyError(str(fact))
        return facts[fact]

    if expression_type == "MULTIPLY_FACT_BY_RATE":
        fact = expression.get("fact")
        if fact not in facts:
            raise KeyError(str(fact))
        value = _decimal(facts[fact], str(fact))
        rate = _decimal(expression.get("rate"), "rate")
        return str(value * rate)

    if expression_type == "ADD_FACTS":
        fact_names = expression.get("facts")
        if not isinstance(fact_names, list) or not fact_names:
            raise ValueError("ADD_FACTS requires facts")
        total = Decimal("0")
        for fact in fact_names:
            if fact not in facts:
                raise KeyError(str(fact))
            total += _decimal(facts[fact], str(fact))
        return str(total)

    fact = expression.get("fact")
    if fact not in facts:
        raise KeyError(str(fact))
    value = _decimal(facts[fact], str(fact))
    threshold = _decimal(expression.get("threshold"), "threshold")
    return value >= threshold


def execute_rule(
    payload: dict[str, Any],
    rule: dict[str, Any],
    corpus_lock: dict[str, Any],
    artifact_hashes: dict[str, str],
) -> dict[str, Any]:
    lock_ok, lock_reason = validate_corpus_lock(corpus_lock, artifact_hashes)
    if not lock_ok:
        return _human(payload, "LOW_CONFIDENCE", lock_reason)

    operation = str(payload.get("operation", "")).upper()
    if operation not in ALLOWED_OPERATIONS:
        return _human(payload, "POLICY_CONFLICT", "Operation is outside the TAX-001 deterministic rule allow-list.")
    if str(rule.get("operation", "")).upper() != operation:
        return _human(payload, "POLICY_CONFLICT", "Rule operation does not match the request operation.")
    if rule.get("jurisdiction") != payload.get("jurisdiction"):
        return _human(payload, "LOW_CONFIDENCE", "Rule jurisdiction does not match the case jurisdiction.")

    try:
        case_date = _parse_date(payload.get("effective_date"), "effective_date")
        effective_from = _parse_date(rule.get("effective_from"), "effective_from")
        effective_to = _parse_date(rule.get("effective_to"), "effective_to")
    except ValueError as exc:
        return _human(payload, "LOW_CONFIDENCE", str(exc))
    if not effective_from <= case_date <= effective_to:
        return _human(payload, "LOW_CONFIDENCE", "No current rule covers the requested effective date.")

    evidence_refs = rule.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs or not all(isinstance(ref, str) and ref.strip() for ref in evidence_refs):
        return _human(payload, "LOW_CONFIDENCE", "Rule has no verified official evidence references.")

    payload_evidence = payload.get("evidence_refs")
    if not isinstance(payload_evidence, list) or not set(evidence_refs).issubset(set(payload_evidence)):
        return _human(payload, "LOW_CONFIDENCE", "Case evidence does not include all evidence bound to the selected rule.", evidence_refs=evidence_refs)

    facts = payload.get("facts")
    if not isinstance(facts, dict):
        return _human(payload, "LOW_CONFIDENCE", "Concrete case facts are required.", evidence_refs=evidence_refs)
    required_facts = rule.get("required_facts")
    if not isinstance(required_facts, list):
        return _human(payload, "POLICY_CONFLICT", "Rule required_facts contract is invalid.", evidence_refs=evidence_refs)
    missing = [fact for fact in required_facts if fact not in facts]
    if missing:
        return _human(payload, "LOW_CONFIDENCE", f"Missing required facts: {', '.join(map(str, missing))}.", evidence_refs=evidence_refs)

    expression = rule.get("expression")
    if not isinstance(expression, dict):
        return _human(payload, "POLICY_CONFLICT", "Rule expression contract is invalid.", evidence_refs=evidence_refs)
    try:
        value = _execute_expression(expression, facts)
    except (ValueError, KeyError) as exc:
        return _human(payload, "LOW_CONFIDENCE", f"Deterministic rule could not execute: {exc}.", evidence_refs=evidence_refs)

    rule_id = rule.get("rule_id")
    rule_version = rule.get("rule_version")
    if not isinstance(rule_id, str) or not rule_id.strip() or not isinstance(rule_version, str) or not rule_version.strip():
        return _human(payload, "POLICY_CONFLICT", "Rule identity/version is invalid.", evidence_refs=evidence_refs)

    return {
        "request_id": str(payload.get("request_id", "")),
        "company_id": str(payload.get("company_id", "")),
        "engine_id": ENGINE_ID,
        "version": VERSION,
        "environment": ENVIRONMENT,
        "status": "RULE_EXECUTED",
        "operation": operation,
        "confidence": 1.0,
        "human_required": None,
        "rule_id": rule_id,
        "rule_version": rule_version,
        "value": value,
        "evidence_refs": evidence_refs,
        "corpus_lock_verified": True,
        "cost_eur": 0.0,
    }
