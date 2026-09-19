from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CEREBRO_OS_ROOT = Path(__file__).resolve().parents[1]
if str(CEREBRO_OS_ROOT) not in sys.path:
    sys.path.insert(0, str(CEREBRO_OS_ROOT))

from quality.tribunal import REQUIRED_GATES, TribunalDecision


def generate() -> list[Path]:
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
        payload = json.loads(candidate_path.read_text(encoding="utf-8"))
        company_id = str(payload.get("company_id", "")).strip()
        if not company_id:
            raise ValueError("candidate payload missing company_id")
        candidates = payload.get("candidates") or []

        evaluate_path = evidence_root / f"{company_id}.evaluate.json"
        evaluate_payload = json.loads(evaluate_path.read_text(encoding="utf-8")) if evaluate_path.exists() else {}
        evaluate_green = (
            str(evaluate_payload.get("company_id", "")) == company_id
            and str(evaluate_payload.get("stage", "")) == "EVALUATE"
            and str(evaluate_payload.get("status", "")) == "GREEN"
            and str(evaluate_payload.get("evaluation_scope", "")) == "SPEC_SAFETY_ONLY"
            and not bool(evaluate_payload.get("outcome_effect_verified", True))
            and not bool(evaluate_payload.get("external_mutation_allowed", True))
        )

        deterministic = bool(candidates) and all(
            str(item.get("company_id", "")) == company_id
            and str(item.get("mode", "")) == "DETERMINISTIC_PATCH_SPEC"
            and not bool(item.get("external_mutation_allowed", True))
            and float(item.get("cost_eur", 0.0)) == 0.0
            for item in candidates
        )

        packet_ref = f"file://{evidence_root / (company_id + '.tribunal.json')}"
        if evaluate_green and deterministic:
            gates = {gate: True for gate in REQUIRED_GATES}
            refs = {
                "contracts": f"file://{candidate_path}#candidate-contract",
                "permissions": f"file://{candidate_path}#no-external-mutation",
                "tests": f"file://{evidence_root / (company_id + '.test.json')}",
                "evaluation": f"file://{evaluate_path}",
                "observability": f"{packet_ref}#structured-audit-packet",
                "rollback": f"{packet_ref}#lab-no-mutation-rollback",
                "backup": f"{packet_ref}#lab-no-mutation-backup",
                "rebuild": f"{packet_ref}#candidate-spec-rebuild",
                "cost": f"{packet_ref}#zero-cost",
                "policy": f"{packet_ref}#lab-read-only-policy",
                "tenant_isolation": f"{packet_ref}#company-{company_id}",
            }
            decision = TribunalDecision(
                engine_id="SUP-IMPROVEMENT",
                gates=gates,
                company_id=company_id,
                environment="LAB",
                evidence_refs=refs,
                version="1.0.0",
            )
            status = "GREEN" if decision.approved else "WAITING"
            missing = decision.missing()
            missing_evidence = decision.missing_evidence()
        else:
            gates = {gate: False for gate in REQUIRED_GATES}
            refs = {}
            status = "WAITING"
            missing = tuple(REQUIRED_GATES)
            missing_evidence = ()

        target = evidence_root / f"{company_id}.tribunal.json"
        target.write_text(json.dumps({
            "company_id": company_id,
            "stage": "TRIBUNAL",
            "status": status,
            "evidence_ref": packet_ref,
            "tribunal_scope": "LAB_SPEC_SAFETY_ONLY",
            "production_approval": False,
            "external_mutation_allowed": False,
            "cost_eur": 0.0,
            "gates": gates,
            "gate_evidence": refs,
            "missing_gates": list(missing),
            "missing_evidence": list(missing_evidence),
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)

    return written


if __name__ == "__main__":
    for path in generate():
        print(path)
