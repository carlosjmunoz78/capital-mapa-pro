from __future__ import annotations

from dataclasses import dataclass

from governance.policy import PolicyRequest, evaluate as evaluate_policy
from learning.continuous_improvement import ImprovementCandidate
from learning.continuous_improvement_runtime import StageResult
from quality.evaluation import EvaluationResult, aggregate
from quality.tribunal import TribunalDecision


@dataclass(frozen=True)
class GovernedImprovementContext:
    candidate: ImprovementCandidate
    evaluations: tuple[EvaluationResult, ...]
    tribunal: TribunalDecision
    policy_request: PolicyRequest
    evidence_by_stage: dict[str, str]


class GovernedImprovementExecutor:
    def __init__(self, context: GovernedImprovementContext) -> None:
        self.context = context

    def __call__(self, stage: str, attempt: int) -> StageResult:
        evidence = str(self.context.evidence_by_stage.get(stage, "")).strip()
        if not evidence:
            return StageResult(stage, "WAITING", f"evidence://waiting/{stage}")

        if stage == "EVALUATE":
            ok = aggregate(
                self.context.evaluations,
                company_id=self.context.candidate.objective.company_id,
                environment=self.context.candidate.objective.environment,
                version=self.context.candidate.objective.version,
            )
            return StageResult(stage, "GREEN" if ok else "RED", evidence)

        if stage == "TRIBUNAL":
            t = self.context.tribunal
            same_scope = (
                t.company_id == self.context.candidate.objective.company_id
                and t.environment == self.context.candidate.objective.environment
                and t.version == self.context.candidate.objective.version
            )
            return StageResult(stage, "GREEN" if t.approved and same_scope else "RED", evidence)

        if stage == "OLD_VS_NEW":
            self.context.candidate.validate()
            return StageResult(stage, "GREEN" if self.context.candidate.improves_baseline else "BLOCKED", evidence)

        if stage == "CANARY":
            decision = evaluate_policy(self.context.policy_request)
            if decision["decision"] == "HUMAN_REQUIRED":
                return StageResult(stage, "HUMAN_REQUIRED", evidence, decision["reasons"][0])
            if decision["decision"] != "ALLOW":
                return StageResult(stage, "BLOCKED", evidence)
            return StageResult(stage, "GREEN", evidence)

        if stage == "PROMOTE_OR_ROLLBACK":
            refs = dict(self.context.candidate.evidence_refs)
            if not str(refs.get("rollback", "")).strip():
                return StageResult(stage, "BLOCKED", evidence)
            return StageResult(stage, "GREEN", evidence)

        return StageResult(stage, "GREEN", evidence)
