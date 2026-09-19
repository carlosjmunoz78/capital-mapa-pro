from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CEREBRO_OS_ROOT = Path(__file__).resolve().parents[1]
if str(CEREBRO_OS_ROOT) not in sys.path:
    sys.path.insert(0, str(CEREBRO_OS_ROOT))


def evaluate() -> list[Path]:
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
        test_path = evidence_root / f"{company_id}.test.json"
        test = json.loads(test_path.read_text(encoding="utf-8")) if test_path.exists() else {}
        test_green = (
            str(test.get("company_id", "")) == company_id
            and str(test.get("stage", "")) == "TEST"
            and str(test.get("status", "")) == "GREEN"
            and str(test.get("test_scope", "")) == "CANDIDATE_CONTRACT_ONLY"
            and not bool(test.get("external_mutation_allowed", True))
        )

        deterministic = bool(candidates) and all(
            str(item.get("mode", "")) == "DETERMINISTIC_PATCH_SPEC"
            and not bool(item.get("external_mutation_allowed", True))
            and float(item.get("cost_eur", 0.0)) == 0.0
            and bool((item.get("change_spec") or {}).get("operation"))
            for item in candidates
        )
        status = "GREEN" if test_green and deterministic else "WAITING"
        reasons: list[str] = []
        if not test_green:
            reasons.append("contract_test_not_green")
        if not deterministic:
            reasons.append("candidate_requires_substantive_evaluation")

        target = evidence_root / f"{company_id}.evaluate.json"
        target.write_text(json.dumps({
            "company_id": company_id,
            "stage": "EVALUATE",
            "status": status,
            "evidence_ref": f"file://{candidate_path}",
            "evaluation_scope": "SPEC_SAFETY_ONLY",
            "outcome_effect_verified": False,
            "external_mutation_allowed": False,
            "cost_eur": 0.0,
            "reasons": reasons,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)

    return written


if __name__ == "__main__":
    for path in evaluate():
        print(path)
