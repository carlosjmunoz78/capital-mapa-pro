from __future__ import annotations

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
        "human_exception_codes": HUMAN_EXCEPTION_CODES,
    }


def scaffold(root: Path, engine_id: str, name: str) -> Path:
    engine_id = validate_engine_id(engine_id)
    target = root / "engines" / engine_id
    if target.exists():
        raise FileExistsError(f"engine already exists: {engine_id}")
    for relative in ["config", "contracts", "policies", "events", "jobs", "api", "tests", "evaluation", "observability", "ops", "docs", "training"]:
        (target / relative).mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(engine_id, name)
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (target / "docs" / "README.md").write_text(f"# {engine_id} · {manifest['name']}\n\nEstado inicial: DEFINED_NOT_BUILT.\n", encoding="utf-8")
    (target / "ops" / "backup.md").write_text("# Backup\n\nPendiente de implementación y prueba.\n", encoding="utf-8")
    (target / "ops" / "rollback.md").write_text("# Rollback\n\nPendiente de implementación y prueba.\n", encoding="utf-8")
    (target / "ops" / "rebuild.md").write_text("# Rebuild\n\nPendiente de implementación y prueba.\n", encoding="utf-8")
    return target


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: python factory.py ENGINE_ID 'Engine Name' [ROOT]", file=sys.stderr)
        return 2
    engine_id, name = argv[1], argv[2]
    root = Path(argv[3]) if len(argv) > 3 else Path(__file__).resolve().parents[1]
    target = scaffold(root, engine_id, name)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
