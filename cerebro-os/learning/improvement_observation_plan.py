from __future__ import annotations

from dataclasses import dataclass

from learning.continuous_improvement_runtime import StageResult

STAGES = (
    "OBSERVE", "MEASURE", "DETECT", "PROPOSE", "LAB", "TEST",
    "EVALUATE", "TRIBUNAL", "OLD_VS_NEW", "CANARY",
    "PROMOTE_OR_ROLLBACK", "LEARN",
)


@dataclass(frozen=True)
class ObservationEnvelope:
    company_id: str
    checked: bool
    source: str
    evidence_ref: str
    status: str
    confidence: float = 1.0
    summary: str = ""

    def validate(self) -> None:
        if not self.company_id.strip() or not self.source.strip() or not self.evidence_ref.strip():
            raise ValueError("observation identity and evidence required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.status not in {"NO_CHANGE", "PROPOSAL_READY", "HUMAN_REQUIRED", "SOURCE_ERROR"}:
            raise ValueError("invalid observation status")


def plan_stage_results(observation: ObservationEnvelope) -> dict[str, StageResult]:
    observation.validate()
    if not observation.checked:
        return {"OBSERVE": StageResult("OBSERVE", "WAITING", observation.evidence_ref)}

    if observation.confidence < 0.8:
        return {
            "OBSERVE": StageResult("OBSERVE", "GREEN", observation.evidence_ref),
            "MEASURE": StageResult("MEASURE", "GREEN", observation.evidence_ref),
            "DETECT": StageResult("DETECT", "HUMAN_REQUIRED", observation.evidence_ref, "LOW_CONFIDENCE"),
        }

    if observation.status == "SOURCE_ERROR":
        return {"OBSERVE": StageResult("OBSERVE", "WAITING", observation.evidence_ref)}

    if observation.status == "HUMAN_REQUIRED":
        return {
            "OBSERVE": StageResult("OBSERVE", "GREEN", observation.evidence_ref),
            "MEASURE": StageResult("MEASURE", "GREEN", observation.evidence_ref),
            "DETECT": StageResult("DETECT", "HUMAN_REQUIRED", observation.evidence_ref, "HIGH_RISK"),
        }

    if observation.status == "PROPOSAL_READY":
        result = {
            "OBSERVE": StageResult("OBSERVE", "GREEN", observation.evidence_ref),
            "MEASURE": StageResult("MEASURE", "GREEN", observation.evidence_ref),
            "DETECT": StageResult("DETECT", "GREEN", observation.evidence_ref),
            "PROPOSE": StageResult("PROPOSE", "GREEN", observation.evidence_ref),
        }
        result["LAB"] = StageResult("LAB", "WAITING", f"{observation.evidence_ref}#lab-required")
        return result

    # NO_CHANGE means the source was actually checked and no candidate was found.
    # The cycle is successful but explicitly no-op; later gates are N/A, not promotions.
    return {
        stage: StageResult(stage, "GREEN", f"{observation.evidence_ref}#no-change/{stage}")
        for stage in STAGES
    }
