"""FACT-001 knowledge contract, additive and offline by construction.

A durable PENDING enrollment request is not authorization from Google,
not a verified API delivery, and not agent qualification.
"""
from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SAFE_AGENT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
FACTORY = "KNOWLEDGE-FACTORY-001"


def _safe_identifier(value: str, kind: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ValueError(f"invalid {kind}")
    return value


def _safe_agent_identifier(value: str, kind: str) -> str:
    if not isinstance(value, str) or not SAFE_AGENT_ID.fullmatch(value):
        raise ValueError(f"invalid {kind}")
    return value


def knowledge_manifest(engine: dict, company_id: str | None = None) -> dict:
    engine_id = _safe_identifier(engine["engine_id"], "engine_id")
    if engine.get("environment") != "LAB":
        raise ValueError("FACT knowledge enrollment only in LAB")
    claim = _safe_identifier(company_id, "company_id") if company_id is not None else None
    version = str(engine["version"])
    if not version.strip():
        raise ValueError("missing version")
    return {
        "schema_version": "1.0.0",
        "factory_id": FACTORY,
        "engine_id": engine_id,
        "department_id": "PENDING_VERIFIED_DEPARTMENT_REGISTRY",
        "company_id": "UNRESOLVED_TRUSTED_FACTORY_CONTEXT",
        "unverified_company_claim": claim,
        "environment": "LAB",
        "version": version,
        "enrollment_status": "PENDING_FACTORY_IAM",
        "knowledge_status": "NOT_INGESTED",
        "trained_agents": 0,
        "certified_agents": 0,
        "source_registry_ref": "PENDING_SOURCE_REGISTRY",
        "gateway_consumer_status": "NOT_AUTHENTICATED",
        "delivery_status": "NOT_SENT",
        "security": {
            "signed_factory_identity_required": True,
            "tenant_scoped_oauth_readonly_required": True,
            "public_endpoint_enabled": False,
            "publish_enabled": False,
            "paid_ai_enabled": False,
            "production_enabled": False,
            "training_is_not_certification": True,
            "cross_company_inheritance_forbidden": True,
        },
    }


def write_knowledge_scaffold(target: Path, engine: dict, company_id: str | None = None) -> None:
    """Write only files in the NEW engine scaffold; never call the network."""
    manifest = knowledge_manifest(engine, company_id)
    config = target / "training" / "knowledge_factory_enrollment.json"
    event = target / "events" / "KNOWLEDGE_ENROLLMENT_REQUESTED.contract.json"
    outbox = target / "jobs" / "knowledge_enrollment.pending.json"
    for file in (config, event, outbox):
        if file.exists():
            raise FileExistsError(f"existing knowledge artifact: {file}")
    payload = {
        "event_type": "KNOWLEDGE_ENROLLMENT_REQUESTED",
        "schema_version": "1.0.0",
        "engine_id": manifest["engine_id"],
        "company_id": manifest["company_id"],
        "environment": manifest["environment"],
        "version": manifest["version"],
        "dispatch_enabled": False,
        "blocked_until": ["VERIFIED_SOURCE_REGISTRY", "FACTORY_SIGNED_IAM", "GOOGLE_SHEETS_READER_OAUTH", "GATEWAY_LAB_POLICY"],
    }
    for file in (config, event, outbox):
        file.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    event.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    outbox.write_text(json.dumps({**payload, "status": "PENDING_NOT_DISPATCHED"}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def register_agent_candidate(target: Path, agent_id: str, subagent_id: str | None = None) -> Path:
    """For agent creators to call. Does not declare training or grant permissions."""
    agent_id = _safe_agent_identifier(agent_id, "agent_id")
    subagent_id = _safe_agent_identifier(subagent_id, "subagent_id") if subagent_id else None
    manifest_file = target / "training" / "knowledge_factory_enrollment.json"
    if not manifest_file.is_file():
        raise FileNotFoundError("missing FACT knowledge contract")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest.get("environment") != "LAB" or manifest.get("enrollment_status") != "PENDING_FACTORY_IAM":
        raise PermissionError("unsafe agent registration context")
    fingerprint = hashlib.sha256(json.dumps([agent_id, subagent_id], ensure_ascii=False).encode("utf-8")).hexdigest()[:24]
    dest = target / "training" / "knowledge_candidates" / f"agent-{fingerprint}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": "1.0.0",
        "company_id": manifest["company_id"],
        "engine_id": manifest["engine_id"],
        "environment": "LAB",
        "version": manifest["version"],
        "agent_id": agent_id,
        "subagent_id": subagent_id,
        "knowledge_status": "PENDING_SOURCE_AND_TRAINING",
        "certification_status": "NOT_CERTIFIED",
        "gateway_consumed": False,
        "permissions_granted": False,
        "dispatch_enabled": False,
    }
    content = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    if dest.exists():
        if dest.read_text(encoding="utf-8") != content:
            raise FileExistsError(f"conflicting agent candidate: {dest}")
        return dest
    dest.write_text(content, encoding="utf-8")
    return dest


def validate_agent_inventory(records: object) -> tuple[tuple[str, str | None], ...]:
    """Validate actual creator output before the engine scaffold writes any files."""
    if not isinstance(records, (list, tuple)):
        raise ValueError("agent inventory must be an array of identity records")
    identities = []
    for entry in records:
        if not isinstance(entry, dict) or set(entry) - {"agent_id", "subagent_id"}:
            raise ValueError("invalid agent inventory record")
        agent_id = _safe_agent_identifier(entry.get("agent_id"), "agent_id")
        subagent_id = entry.get("subagent_id")
        if subagent_id is not None:
            subagent_id = _safe_agent_identifier(subagent_id, "subagent_id")
        identities.append((agent_id, subagent_id))
    return tuple(dict.fromkeys(identities))
