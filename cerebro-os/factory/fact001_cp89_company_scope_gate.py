"""CP89 FACT-001 company-scope gate.

Fail-closed bridge between the canonical company registry and the CP88 physical
LAB instance. This module never creates aliases, grants IAM, dispatches UMS, or
changes runtime state.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

COMPANY_RE = re.compile(r"^[a-z][a-z0-9-]{1,62}$")
EXPECTED_ENGINE = "SUP-001"
EXPECTED_ENV = "LAB"
ADMIN_SEED = "ADMIN_READONLY_EVIDENCE_SEED"


def _company_id(value: object) -> str:
    if not isinstance(value, str) or not COMPANY_RE.fullmatch(value):
        raise ValueError("CP89_INVALID_COMPANY_ID")
    return value


def find_canonical_company(registry_rows: Iterable[Mapping], legal_name: str) -> Mapping:
    matches = [row for row in registry_rows if row.get("legal_name") == legal_name]
    if len(matches) != 1:
        raise ValueError("CP89_CANONICAL_COMPANY_NOT_UNIQUE")
    _company_id(matches[0].get("company_id"))
    return matches[0]


def assess_company_scope(*, registry_company_id: str, runtime_company_id: str) -> dict:
    registry_id = _company_id(registry_company_id)
    runtime_id = _company_id(runtime_company_id)
    matched = registry_id == runtime_id
    return {
        "status": "SAME_CANONICAL_COMPANY_ID" if matched else "HOLD_COMPANY_ID_MISMATCH",
        "registry_company_id": registry_id,
        "runtime_company_id": runtime_id,
        "aliases_automatically_assumed": False,
        "cross_company_action_allowed": False,
        "attribution_to_registry_allowed": matched,
        "verified_alias_contract_required": not matched,
    }


def assess_cp89_provisioning(*, registry_rows: Iterable[Mapping], instance: Mapping) -> dict:
    if instance.get("engine_id") != EXPECTED_ENGINE or instance.get("environment") != EXPECTED_ENV:
        raise ValueError("CP89_INSTANCE_SCOPE_INVALID")
    canonical = find_canonical_company(registry_rows, "Fenix Capital")
    scope = assess_company_scope(
        registry_company_id=canonical["company_id"],
        runtime_company_id=instance.get("company_id"),
    )
    if scope["status"] != "SAME_CANONICAL_COMPANY_ID":
        return {
            **scope,
            "factory_provisioning_allowed": False,
            "iam_grant_allowed": False,
            "ums_enrollment_allowed": False,
            "next_gate": "VERIFIED_SIGNED_COMPANY_ID_CONTRACT",
        }
    if instance.get("registration_method") == ADMIN_SEED:
        return {
            **scope,
            "status": "HOLD_NOT_FACTORY_PROVISIONED",
            "factory_provisioning_allowed": False,
            "iam_grant_allowed": False,
            "ums_enrollment_allowed": False,
            "next_gate": "AUTHORIZED_FACTORY_ISSUER",
        }
    return {
        **scope,
        "status": "READY_FOR_AUTHORIZED_FACTORY_GATE",
        "factory_provisioning_allowed": False,
        "iam_grant_allowed": False,
        "ums_enrollment_allowed": False,
        "next_gate": "AUTHORIZED_FACTORY_ISSUER",
    }
