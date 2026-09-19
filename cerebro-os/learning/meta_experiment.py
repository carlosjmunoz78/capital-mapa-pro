from __future__ import annotations

from dataclasses import dataclass

SAFE_ACTIONS = {
    "OBSERVE": "INCREASE_OBSERVATION_COVERAGE",
    "MEASURE": "IMPROVE_MEASUREMENT_FIDELITY",
    "DETECT": "ADD_DETERMINISTIC_DETECTION_SIGNAL",
    "PROPOSE": "IMPROVE_PROPOSAL_PRIORITIZATION",
    "LAB": "ADD_LAB_REHEARSAL_CASE",
    "TEST": "ADD_CONTRACT_TEST_COVERAGE",
    "EVALUATE": "ADD_INDEPENDENT_EVALUATION_EVIDENCE",
    "TRIBUNAL": "ADD_TRIBUNAL_EVIDENCE_CLARITY",
    "OLD_VS_NEW": "ADD_STRUCTURAL_COMPARISON_SIGNAL",
    "CANARY": "ADD_LOCAL_CANARY_SCENARIO",
    "PROMOTE_OR_ROLLBACK": "IMPROVE_ROLLBACK_EVIDENCE",
    "LEARN": "IMPROVE_LEARNING_RECORD_FIDELITY",
}

@dataclass(frozen=True)
class MetaExperiment:
    company_id: str
    environment: str
    version: str
    bottleneck_stage: str
    experiment_id: str
    action: str
    objective: str
    control_strategy_version: str
    candidate_strategy_version: str
    independent_holdout_required: bool
    judge_independence_required: bool
    policy_weakening_allowed: bool
    permission_escalation_allowed: bool
    threshold_reduction_allowed: bool
    auto_apply_allowed: bool
    external_mutation_allowed: bool
    cost_eur: float

def build(meta: dict) -> MetaExperiment | None:
    if str(meta.get("decision", "")) != "PROPOSE_META_EXPERIMENT":
        return None
    company_id = str(meta.get("company_id", "")).strip()
    environment = str(meta.get("environment", "")).strip()
    version = str(meta.get("version", "")).strip()
    stage = str(meta.get("bottleneck_stage", "")).strip()
    if not all((company_id, environment, version, stage)):
        raise ValueError("complete meta-learning scope required")
    if stage not in SAFE_ACTIONS:
        raise ValueError("unsupported bottleneck stage")
    prior = str(meta.get("prior_strategy_version", "meta-v0")).strip() or "meta-v0"
    candidate = str(meta.get("candidate_strategy_version", f"{prior}-candidate-1")).strip()
    action = SAFE_ACTIONS[stage]
    return MetaExperiment(
        company_id=company_id,
        environment=environment,
        version=version,
        bottleneck_stage=stage,
        experiment_id=f"{company_id}:{environment}:{version}:{stage}:{candidate}",
        action=action,
        objective=f"Reduce validated friction at {stage} without weakening any independent gate.",
        control_strategy_version=prior,
        candidate_strategy_version=candidate,
        independent_holdout_required=True,
        judge_independence_required=True,
        policy_weakening_allowed=False,
        permission_escalation_allowed=False,
        threshold_reduction_allowed=False,
        auto_apply_allowed=False,
        external_mutation_allowed=False,
        cost_eur=0.0,
    )
