from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ENGINE_DIR = Path(__file__).resolve().parents[1]


def evaluate_capability(
    manifest: dict[str, Any],
    corpus_lock: dict[str, Any],
    *,
    aud001_available: bool,
) -> dict[str, Any]:
    blockers: list[str] = []

    if manifest.get("engine_id") != "TAX-001":
        blockers.append("ENGINE_ID_MISMATCH")
    if manifest.get("environment") != "LAB":
        blockers.append("LAB_ONLY_REQUIRED")
    if manifest.get("knowledge_status") != "KNOWLEDGE_GREEN":
        blockers.append("KNOWLEDGE_NOT_GREEN")
    if manifest.get("corpus_lock_status") != "BOUND":
        blockers.append("CORPUS_LOCK_NOT_BOUND")
    if corpus_lock.get("status") != "BOUND":
        blockers.append("CORPUS_ARTIFACTS_NOT_BOUND")
    if not aud001_available:
        blockers.append("AUD001_NOT_AVAILABLE")
    if manifest.get("audit_persistence_status") != "VERIFIED_LAB":
        blockers.append("AUDIT_PERSISTENCE_NOT_VERIFIED")

    for gate in ("backup", "rollback", "rebuild"):
        gate_value = manifest.get(gate)
        if not isinstance(gate_value, dict) or gate_value.get("verified") is not True:
            blockers.append(f"{gate.upper()}_NOT_VERIFIED")

    if manifest.get("prod_enabled") is not False:
        blockers.append("PROD_MUST_REMAIN_DISABLED_DURING_CAPABILITY_TRIBUNAL")
    if manifest.get("autonomy_status") != "DISABLED":
        blockers.append("AUTONOMY_MUST_REMAIN_DISABLED")

    return {
        "engine_id": "TAX-001",
        "gate": "CAPABILITY_TRIBUNAL",
        "status": "PASS" if not blockers else "FAIL_CLOSED",
        "blockers": blockers,
        "capability_green": not blockers,
        "autonomy_green": False,
        "prod_enabled": False,
    }


def evaluate_current() -> dict[str, Any]:
    manifest = json.loads((ENGINE_DIR / "manifest.json").read_text(encoding="utf-8"))
    corpus_lock = json.loads((ENGINE_DIR / "config" / "corpus_lock.json").read_text(encoding="utf-8"))
    aud_manifest = ENGINE_DIR.parent / "AUD-001" / "manifest.json"
    return evaluate_capability(manifest, corpus_lock, aud001_available=aud_manifest.exists())


if __name__ == "__main__":
    print(json.dumps(evaluate_current(), sort_keys=True))
