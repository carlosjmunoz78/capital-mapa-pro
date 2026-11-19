from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HUMAN_EXCEPTION_CODES = [
    "LEGAL_REQUIRED",
    "SIGNATURE_REQUIRED",
    "LOW_CONFIDENCE",
    "HIGH_RISK",
    "POLICY_CONFLICT",
    "SECURITY_INCIDENT",
    "MONEY_LIMIT",
    "CUSTOMER_HUMAN_REQUEST",
]

ENGINE_ID_RE = re.compile(r"^[A-Z0-9-]+$")


def validate_engine_id(engine_id: str) -> str:
    engine_id = engine_id.strip().upper()
    if not ENGINE_ID_RE.match(engine_id):
        raise ValueError("engine_id must use A-Z, 0-9 and hyphen only")
    return engine_id


def build_manifest(engine_id: str, name: str) -> dict:
    engine_id = validate_engine_id(engine_id)
    return {
        "engine_id": engine_id,
        "name": name.strip() or engine_id,
        "company_scope": "GLOBAL_OR_SCOPED",
        "environment": "LAB",
        "version": "0.1.0",
        "status": "DEFINED_NOT_BUILT",
        "owner": "UNASSIGNED",
        "inputs": [],
        "outputs": [],
        "permissions": [],
        "policies": ["deny_cross_company_by_default", "deterministic_before_ai", "zero_new_cost_by_default"],
        "events_in": [],
        "events_out": [],
        "tests": ["unit", "contract", "integration"],
        "evaluation": ["policy_gate", "tribunal_gate"],
        "observability": ["request_id", "company_id", "engine_id", "version", "environment", "result", "duration_ms", "cost_eur"],
        "cost_budget": {"target_additional_eur": 0},
        "backup": {"required": True, "verified": False},
        "rollback": {"required": True, "verified": False},
        "rebuild": {"required": True, "verified": False},
        "dependencies": [],
        "autonomy_level": "MANUAL_WITH_APPROVAL",
        "media_gateway": {
            "provider_engine_id": "UMS-001",
            "connection": "CEREBRO_GATEWAY_UNIVERSAL",
            "provisioner": "FACT-001",
            "enrollment": "AUTOMATIC_ON_ENGINE_CREATE_WHEN_FACTORY_IAM_READY",
            "enrollment_status": "PENDING_FACTORY_IAM",
            "capabilities": ["IMAGE.SYNTHETIC"],
            "uses_per_engine_worker": False,
            "uses_per_engine_subscription": False,
            "publish_authorized": False,
            "paid_execution_enabled": False,
            "version": "1.0.0"
        },
        "human_exception_codes": HUMAN_EXCEPTION_CODES,
    }


def scaffold(root: Path, engine_id: str, name: str, company_id: str | None = None, *,
             agent_inventory: object = ()) -> Path:
    engine_id = validate_engine_id(engine_id)
    knowledge_hook = Path(__file__).with_name("knowledge_factory_hook.py")
    knowledge_spec = importlib.util.spec_from_file_location("cerebro_knowledge_factory_hook", knowledge_hook)
    if knowledge_spec is None or knowledge_spec.loader is None:
        raise RuntimeError("knowledge factory hook unavailable")
    knowledge_module = importlib.util.module_from_spec(knowledge_spec)
    knowledge_spec.loader.exec_module(knowledge_module)
    candidates = knowledge_module.validate_agent_inventory(agent_inventory)
    target = root / "engines" / engine_id
    if target.exists():
        raise FileExistsError(f"engine already exists: {engine_id}")
    for relative in ["config", "contracts", "policies", "events", "jobs", "api", "tests", "evaluation", "observability", "ops", "docs", "training"]:
        (target / relative).mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(engine_id, name)
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Universal UMS-001 hook: new engines automatically inherit the same media contract.
    # This does not self-authorize an engine, create a Worker, or expose credentials.
    # Works both as a package import and via "python factory.py ..."
    media_hook = Path(__file__).with_name("universal_media_hook.py")
    spec = importlib.util.spec_from_file_location("cerebro_universal_media_hook", media_hook)
    if spec is None or spec.loader is None:
        raise RuntimeError("universal media hook unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.write_universal_media_scaffold(target, manifest)
    # Enrollment outbox and automatic delivery through the shared FACT-001 transport.
    # Missing credentials leave a durable PENDING receipt; never bypass Gateway IAM.
    enrollment_hook = Path(__file__).with_name("universal_media_enrollment.py")
    enroll_spec = importlib.util.spec_from_file_location("cerebro_factory_media_enrollment", enrollment_hook)
    if enroll_spec is None or enroll_spec.loader is None:
        raise RuntimeError("universal media enrollment hook unavailable")
    enroll_module = importlib.util.module_from_spec(enroll_spec)
    enroll_spec.loader.exec_module(enroll_module)
    enroll_module.enroll_factory_engine(target, manifest, company_id=company_id)
    # KNOWLEDGE-FACTORY-001: durable LAB requests for this engine and its declared identities.
    knowledge_module.write_knowledge_scaffold(target, manifest, company_id=company_id)
    for agent_id, subagent_id in candidates:
        knowledge_module.register_agent_candidate(target, agent_id, subagent_id)
    (target / "docs" / "README.md").write_text(f"# {engine_id} · {manifest['name']}\n\nEstado inicial: DEFINED_NOT_BUILT.\n", encoding="utf-8")
    (target / "ops" / "backup.md").write_text("# Backup\n\nPendiente de implementación y prueba.\n", encoding="utf-8")
    (target / "ops" / "rollback.md").write_text("# Rollback\n\nPendiente de implementación y prueba.\n", encoding="utf-8")
    (target / "ops" / "rebuild.md").write_text("# Rebuild\n\nPendiente de implementación y prueba.\n", encoding="utf-8")
    return target


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Scaffold a LAB engine and enqueue knowledge candidates")
    parser.add_argument("engine_id")
    parser.add_argument("name")
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("company_id", nargs="?")
    parser.add_argument("--agents-json", type=Path, help="Creator's JSON array of agent_id/subagent_id records")
    args = parser.parse_args(argv[1:])
    inventory = json.loads(args.agents_json.read_text(encoding="utf-8")) if args.agents_json else ()
    target = scaffold(args.root, args.engine_id, args.name, company_id=args.company_id, agent_inventory=inventory)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
