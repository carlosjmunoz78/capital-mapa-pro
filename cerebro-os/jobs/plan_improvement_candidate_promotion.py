from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CEREBRO_OS_ROOT = Path(__file__).resolve().parents[1]
if str(CEREBRO_OS_ROOT) not in sys.path:
    sys.path.insert(0, str(CEREBRO_OS_ROOT))


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("payload must be object")
    return payload


def _rollback_for(item: dict) -> dict:
    spec = item.get("change_spec") or {}
    operation = str(spec.get("operation", ""))
    target = str(item.get("target", ""))
    if operation == "SET_CANONICAL":
        return {
            "operation": "RESTORE_PREVIOUS_CANONICAL",
            "target": target,
            "requires_baseline_snapshot": True,
        }
    if operation == "ADD_SITEMAP_REFERENCE":
        return {
            "operation": "REMOVE_SITEMAP_REFERENCE",
            "target": target,
            "requires_baseline_snapshot": True,
        }
    return {
        "operation": "UNSUPPORTED_AUTOMATIC_ROLLBACK",
        "target": target,
        "requires_baseline_snapshot": True,
    }


def plan() -> list[Path]:
    candidates_root = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_CANDIDATES_ROOT",
        ".cerebro-runtime/candidates",
    ))
    evidence_root = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_EVIDENCE_ROOT",
        ".cerebro-runtime/evidence",
    ))
    evidence_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for candidate_path in sorted(candidates_root.glob("*.json")):
        candidate_payload = _load(candidate_path)
        company_id = str(candidate_payload.get("company_id", "")).strip()
        if not company_id:
            raise ValueError("candidate payload missing company_id")

        tribunal = _load(evidence_root / f"{company_id}.tribunal.json")
        canary = _load(evidence_root / f"{company_id}.canary.json")
        if tribunal and str(tribunal.get("company_id", "")) != company_id:
            raise ValueError("cross-company TRIBUNAL evidence denied")
        if canary and str(canary.get("company_id", "")) != company_id:
            raise ValueError("cross-company CANARY evidence denied")

        candidates = candidate_payload.get("candidates") or []
        rollback_plan = [
            {
                "proposal_id": str(item.get("proposal_id", "")),
                **_rollback_for(item),
            }
            for item in candidates
        ]
        rollback_supported = bool(candidates) and all(
            item["operation"] != "UNSUPPORTED_AUTOMATIC_ROLLBACK"
            for item in rollback_plan
        )

        tribunal_green = (
            str(tribunal.get("stage", "")) == "TRIBUNAL"
            and str(tribunal.get("status", "")) == "GREEN"
            and not bool(tribunal.get("production_approval", True))
            and not bool(tribunal.get("external_mutation_allowed", True))
        )
        local_canary_green = (
            str(canary.get("stage", "")) == "CANARY"
            and str(canary.get("status", "")) == "GREEN"
            and str(canary.get("canary_scope", "")) == "LOCAL_SIMULATION_ONLY"
            and not bool(canary.get("live_traffic_exposed", True))
            and not bool(canary.get("live_effect_verified", True))
            and not bool(canary.get("production_ready", True))
            and not bool(canary.get("external_mutation_allowed", True))
        )

        status = "WAITING"
        decision = "HOLD_FOR_LIVE_CANARY"
        reasons = ["LIVE_EFFECT_NOT_VERIFIED"]
        if not tribunal_green:
            decision = "HOLD_FOR_TRIBUNAL"
            reasons = ["TRIBUNAL_NOT_GREEN"]
        elif not local_canary_green:
            decision = "HOLD_FOR_CANARY"
            reasons = ["CANARY_NOT_GREEN"]
        elif not rollback_supported:
            decision = "HOLD_FOR_ROLLBACK"
            reasons = ["AUTOMATIC_ROLLBACK_UNSUPPORTED"]

        target_path = evidence_root / f"{company_id}.promote_or_rollback.json"
        target_path.write_text(json.dumps({
            "company_id": company_id,
            "stage": "PROMOTE_OR_ROLLBACK",
            "status": status,
            "decision": decision,
            "reasons": reasons,
            "evidence_ref": f"file://{candidate_path}",
            "promotion_allowed": False,
            "progressive_delivery_allowed": False,
            "live_effect_verified": False,
            "production_ready": False,
            "external_mutation_allowed": False,
            "post_promotion_monitoring_required": True,
            "rollback_supported": rollback_supported,
            "rollback_plan": rollback_plan,
            "cost_eur": 0.0,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target_path)

    return written


if __name__ == "__main__":
    for path in plan():
        print(path)
