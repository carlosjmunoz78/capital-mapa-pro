from __future__ import annotations

import json
import os
from pathlib import Path

FACTORY_ACTIONS = {
    "ADD_CONTRACT_TEST_COVERAGE",
    "ADD_LAB_REHEARSAL_CASE",
    "ADD_LOCAL_CANARY_SCENARIO",
}
SUPERVISOR_ACTIONS = {
    "INCREASE_OBSERVATION_COVERAGE",
    "IMPROVE_MEASUREMENT_FIDELITY",
    "ADD_DETERMINISTIC_DETECTION_SIGNAL",
    "IMPROVE_PROPOSAL_PRIORITIZATION",
    "ADD_INDEPENDENT_EVALUATION_EVIDENCE",
    "ADD_TRIBUNAL_EVIDENCE_CLARITY",
    "ADD_STRUCTURAL_COMPARISON_SIGNAL",
    "IMPROVE_ROLLBACK_EVIDENCE",
    "IMPROVE_LEARNING_RECORD_FIDELITY",
}


def target_engine(action: str) -> str:
    if action in FACTORY_ACTIONS:
        return "FACT-001"
    if action in SUPERVISOR_ACTIONS:
        return "SUP-001"
    raise ValueError("unsupported meta-experiment action")


def run() -> list[Path]:
    source_root = Path(os.environ.get(
        "CEREBRO_META_EXPERIMENT_ROOT",
        ".cerebro-runtime/meta-experiments",
    ))
    out_root = Path(os.environ.get(
        "CEREBRO_SELF_IMPROVEMENT_ROOT",
        ".cerebro-runtime/self-improvement-candidates",
    ))
    out_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for path in sorted(source_root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("meta-experiment payload must be object")
        company_id = str(payload.get("company_id", "")).strip()
        environment = str(payload.get("environment", "")).strip()
        version = str(payload.get("version", "")).strip()
        action = str(payload.get("action", "")).strip()
        if not all((company_id, environment, version, action)):
            raise ValueError("complete self-improvement scope required")
        if str(payload.get("status", "")) != "CANDIDATE_ONLY":
            raise ValueError("self-improvement input must remain candidate-only")
        if bool(payload.get("auto_apply_allowed", True)):
            raise ValueError("meta-experiment cannot auto-apply")
        if bool(payload.get("external_mutation_allowed", True)):
            raise ValueError("meta-experiment cannot allow external mutation")
        if not bool(payload.get("independent_holdout_required", False)):
            raise ValueError("independent holdout required")
        if not bool(payload.get("judge_independence_required", False)):
            raise ValueError("independent judge required")
        if bool(payload.get("policy_weakening_allowed", True)):
            raise ValueError("policy weakening forbidden")
        if bool(payload.get("permission_escalation_allowed", True)):
            raise ValueError("permission escalation forbidden")
        if bool(payload.get("threshold_reduction_allowed", True)):
            raise ValueError("threshold reduction forbidden")

        engine_id = target_engine(action)
        candidate = {
            "record_type": "engine_self_improvement_candidate",
            "company_id": company_id,
            "engine_id": engine_id,
            "environment": environment,
            "version": version,
            "source_experiment_id": str(payload.get("experiment_id", "")),
            "action": action,
            "status": "CANDIDATE_ONLY",
            "auto_apply_allowed": False,
            "external_mutation_allowed": False,
            "production_ready": False,
            "policy_change_allowed": False,
            "permission_change_allowed": False,
            "judge_change_allowed": False,
            "budget_change_allowed": False,
            "requires_factory_versioning": engine_id == "FACT-001",
            "requires_supervisor_shadow_validation": engine_id == "SUP-001",
            "required_gates": [
                "contract_tests",
                "independent_evaluation",
                "tribunal",
                "old_vs_new",
                "rollback",
                "backup_rebuild",
                "observability",
            ],
            "cost_eur": 0.0,
        }
        target = out_root / f"{company_id}.{engine_id.lower()}.json"
        target.write_text(json.dumps(candidate, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)
    return written


if __name__ == "__main__":
    for path in run():
        print(path)
