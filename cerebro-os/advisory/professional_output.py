from __future__ import annotations

from dataclasses import dataclass

from .models import AdvisoryDecision
from .source_policy import SourceAssessment


@dataclass(frozen=True)
class ProfessionalAdvisoryOutput:
    case_id: str
    overall_status: str
    domains: tuple[str, ...]
    executive_summary: tuple[str, ...]
    risks: tuple[str, ...]
    deadlines: tuple[str, ...]
    next_actions: tuple[str, ...]
    source_ids: tuple[str, ...]
    human_required: tuple[str, ...]
    audit_refs: tuple[str, ...]

    def validate(self) -> None:
        if not self.case_id.strip() or not self.domains:
            raise ValueError("case_id and domains required")
        if self.overall_status not in {"GREEN", "AMBER", "RED", "BLOCKED", "HUMAN_REQUIRED"}:
            raise ValueError("invalid overall_status")


def normalize_professional_output(
    decision: AdvisoryDecision,
    source_assessment: SourceAssessment,
) -> ProfessionalAdvisoryOutput:
    decision.validate()
    summaries = tuple(opinion.summary for opinion in decision.opinions)
    risks = tuple(item for opinion in decision.opinions for item in opinion.risks)
    deadlines = tuple(item for opinion in decision.opinions for item in opinion.deadlines)
    next_actions = tuple(item for opinion in decision.opinions for item in opinion.next_actions)
    human_required = tuple(
        dict.fromkeys(
            item
            for item in (
                *(opinion.human_exception for opinion in decision.opinions),
                source_assessment.human_exception,
            )
            if item is not None
        )
    )
    overall_status = (
        "HUMAN_REQUIRED"
        if source_assessment.status == "HUMAN_REQUIRED" or human_required
        else decision.overall_status
    )
    output = ProfessionalAdvisoryOutput(
        case_id=decision.case_id,
        overall_status=overall_status,
        domains=decision.domains,
        executive_summary=summaries,
        risks=risks,
        deadlines=deadlines,
        next_actions=next_actions,
        source_ids=source_assessment.accepted_source_ids,
        human_required=human_required,
        audit_refs=decision.audit_refs,
    )
    output.validate()
    return output
