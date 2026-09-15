from __future__ import annotations

from dataclasses import dataclass, replace

from .handlers import build_lab_handlers
from .representative_cases import REPRESENTATIVE_CASE_SPECS, build_representative_case
from .runtime import execute_case


@dataclass(frozen=True)
class ShadowReplayResult:
    case_id: str
    expected_status: str
    actual_status: str
    deterministic_match: bool
    audit_refs: tuple[str, ...]


# Non-production replay contract: run the same evidence-backed representative
# cases twice and require deterministic routing/status. Then perturb evidence on
# one replay and require fail-closed BLOCKED behavior. No App/CRM/PROD access.

def _execute(case):
    handlers = build_lab_handlers(case.requested_domains)
    audit_refs = (
        f"shadow://{case.case_id}/route",
        f"shadow://{case.case_id}/evidence",
        f"shadow://{case.case_id}/coordination",
    )
    decision = execute_case(case, handlers, audit_refs=audit_refs)
    decision.validate()
    return decision


def run_shadow_replay_suite() -> tuple[ShadowReplayResult, ...]:
    results: list[ShadowReplayResult] = []
    for spec in REPRESENTATIVE_CASE_SPECS:
        original = build_representative_case(spec)
        first = _execute(original)
        replay = _execute(original)
        results.append(
            ShadowReplayResult(
                case_id=original.case_id,
                expected_status=first.overall_status,
                actual_status=replay.overall_status,
                deterministic_match=(
                    first.overall_status == replay.overall_status
                    and first.domains == replay.domains
                    and tuple(op.status for op in first.opinions)
                    == tuple(op.status for op in replay.opinions)
                ),
                audit_refs=replay.audit_refs,
            )
        )
    return tuple(results)


def run_fail_closed_shadow_probe() -> str:
    case = build_representative_case(REPRESENTATIVE_CASE_SPECS[0])
    engine_evidence = dict(case.facts["engine_evidence"])
    first_engine = next(iter(engine_evidence))
    engine_evidence[first_engine] = ()
    facts = dict(case.facts)
    facts["engine_evidence"] = engine_evidence
    probe = replace(case, case_id="LAB-SHADOW-MISSING-EVIDENCE-001", facts=facts)
    return _execute(probe).overall_status


def shadow_replay_green() -> bool:
    results = run_shadow_replay_suite()
    return (
        len(results) == len(REPRESENTATIVE_CASE_SPECS)
        and all(result.expected_status == "GREEN" for result in results)
        and all(result.actual_status == "GREEN" for result in results)
        and all(result.deterministic_match for result in results)
        and all(result.audit_refs for result in results)
        and run_fail_closed_shadow_probe() == "BLOCKED"
    )
