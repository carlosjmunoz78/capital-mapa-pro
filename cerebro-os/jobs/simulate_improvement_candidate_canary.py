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


def simulate() -> list[Path]:
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
        candidates = candidate_payload.get("candidates") or []

        old_vs_new = _load(evidence_root / f"{company_id}.old_vs_new.json")
        comparison_green = (
            str(old_vs_new.get("company_id", "")) == company_id
            and str(old_vs_new.get("stage", "")) == "OLD_VS_NEW"
            and str(old_vs_new.get("status", "")) == "GREEN"
            and str(old_vs_new.get("comparison_scope", "")) == "STRUCTURAL_SPEC_ONLY"
            and not bool(old_vs_new.get("live_effect_verified", True))
            and not bool(old_vs_new.get("production_ready", True))
        )

        simulations: list[dict] = []
        all_green = comparison_green and bool(candidates)
        for item in candidates:
            spec = item.get("change_spec") or {}
            operation = str(spec.get("operation", ""))
            target = str(item.get("target", ""))
            passed = False
            simulated_state: dict = {}

            if operation == "SET_CANONICAL":
                value = str(spec.get("value", "")).strip()
                simulated_state = {"canonical": value}
                passed = bool(value) and value == target
            elif operation == "ADD_SITEMAP_REFERENCE":
                simulated_state = {"robots_mentions_sitemap": True}
                passed = True

            simulations.append({
                "proposal_id": str(item.get("proposal_id", "")),
                "operation": operation,
                "target": target,
                "passed": passed,
                "simulated_state": simulated_state,
            })
            all_green = all_green and passed

        target_path = evidence_root / f"{company_id}.canary.json"
        target_path.write_text(json.dumps({
            "company_id": company_id,
            "stage": "CANARY",
            "status": "GREEN" if all_green else "WAITING",
            "evidence_ref": f"file://{candidate_path}",
            "canary_scope": "LOCAL_SIMULATION_ONLY",
            "live_traffic_exposed": False,
            "live_effect_verified": False,
            "external_mutation_allowed": False,
            "production_ready": False,
            "cost_eur": 0.0,
            "simulations": simulations,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target_path)

    return written


if __name__ == "__main__":
    for path in simulate():
        print(path)
