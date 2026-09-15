from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .case_context import CaseSnapshot, CaseStore
from .gateway import AdvisoryGatewayRequest, execute_gateway_request
from .handlers import build_lab_handlers
from .integration_events import AdvisoryIntegrationEvent, IntegrationOutbox
from .models import AdvisoryDecision, DomainOpinion, Territory
from .professional_output import normalize_professional_output
from .representative_cases import (
    REPRESENTATIVE_CASE_SPECS,
    build_representative_case,
    representative_suite_coverage,
    run_representative_case_suite,
)
from .runtime import execute_case
from .source_policy import SourceAssessment, SourceRecord, assess_sources


@dataclass(frozen=True)
class E2EValidationResult:
    checks: dict[str, bool]
    representative_domains: tuple[str, ...]
    representative_cases: int

    @property
    def green(self) -> bool:
        return bool(self.checks) and all(self.checks.values())


def _human_exception_output(code: str) -> bool:
    decision = AdvisoryDecision(
        case_id=f"CASE-{code}",
        domains=("FISCAL",),
        opinions=(
            DomainOpinion(
                domain="FISCAL",
                status="HUMAN_REQUIRED",
                summary=f"Escalation {code}",
                source_refs=("SRC-VALID",),
                human_exception=code,
            ),
        ),
        overall_status="HUMAN_REQUIRED",
        audit_refs=(f"audit://{code}",),
    )
    assessment = SourceAssessment(
        status="GREEN",
        human_exception=None,
        accepted_source_ids=("SRC-VALID",),
        reasons=(),
    )
    output = normalize_professional_output(decision, assessment)
    return output.overall_status == "HUMAN_REQUIRED" and code in output.human_required


def run_e2e_validation() -> E2EValidationResult:
    checks: dict[str, bool] = {}

    representative = run_representative_case_suite()
    coverage = representative_suite_coverage()
    checks["representative_12_domain_coverage"] = len(coverage) == 12
    checks["representative_cases_green"] = (
        len(representative) == len(REPRESENTATIVE_CASE_SPECS)
        and all(result.overall_status == "GREEN" for result in representative)
    )
    checks["multidomain_execution"] = any(len(result.routed_domains) > 1 for result in representative)

    # OLD vs NEW: preserved direct runtime path versus the new Gateway boundary.
    case = build_representative_case(REPRESENTATIVE_CASE_SPECS[0])
    handlers = build_lab_handlers(case.requested_domains)
    old_decision = execute_case(case, handlers, audit_refs=("audit://old",))
    request = AdvisoryGatewayRequest(
        company_id=case.company_id,
        component_id="PROFESSIONAL_ADVISORY",
        engine_id="TAX-001",
        environment=case.environment,
        version=case.version,
        case_id=case.case_id,
        correlation_id="CORR-E2E-OLD-NEW",
        actor={"actor_id": "E2E", "actor_type": "SYSTEM"},
        context={"validation": "old-vs-new"},
        permissions=("advisory:execute",),
        requested_service=case.requested_service,
        territory=case.territory,
        facts=case.facts,
        evidence=case.evidence,
        requested_domains=case.requested_domains,
    )
    new_response = execute_gateway_request(request, handlers, audit_refs=("audit://new",))
    checks["old_vs_new_domains_match"] = old_decision.domains == new_response.decision.domains
    checks["old_vs_new_status_match"] = old_decision.overall_status == new_response.decision.overall_status

    # Multi-company isolation and existing-case recovery.
    store = CaseStore()
    store.save(
        CaseSnapshot(
            company_id="COMPANY-A",
            case_id="SHARED-ID",
            environment="PREPROD",
            version="1.0.0",
            facts={"owner": "A"},
        )
    )
    store.save(
        CaseSnapshot(
            company_id="COMPANY-B",
            case_id="SHARED-ID",
            environment="PREPROD",
            version="1.0.0",
            facts={"owner": "B"},
        )
    )
    checks["multi_company_isolation"] = (
        store.recover("COMPANY-A", "SHARED-ID").facts["owner"] == "A"
        and store.recover("COMPANY-B", "SHARED-ID").facts["owner"] == "B"
    )
    checks["existing_case_recovery"] = store.exists("COMPANY-A", "SHARED-ID")

    outdated = SourceRecord(
        source_id="SRC-OLD",
        source_type="LIVE_SOURCE",
        locator="https://example.invalid/old",
        jurisdiction="ES",
        checked_at="2025-01-01",
        confidence=0.99,
        valid_to="2025-12-31",
    )
    source_assessment = assess_sources(
        (outdated,),
        required_jurisdiction="ES",
        as_of=date(2026, 9, 15),
        require_live_source=True,
    )
    checks["outdated_source_fails_closed"] = (
        source_assessment.status == "HUMAN_REQUIRED"
        and source_assessment.human_exception == "LOW_CONFIDENCE"
    )
    checks["low_confidence_gate"] = checks["outdated_source_fails_closed"]

    checks["high_risk_human_exception"] = _human_exception_output("HIGH_RISK")
    checks["signature_required_human_exception"] = _human_exception_output("SIGNATURE_REQUIRED")
    checks["legal_required_human_exception"] = _human_exception_output("LEGAL_REQUIRED")

    outbox = IntegrationOutbox()
    event = AdvisoryIntegrationEvent(
        event_id="EVT-E2E-001",
        idempotency_key="COMPANY-A:SHARED-ID:CRM:UPDATED",
        correlation_id="CORR-E2E-IDEMPOTENCY",
        company_id="COMPANY-A",
        case_id="SHARED-ID",
        target="CRM",
        event_type="ADVISORY_CASE_UPDATED",
        payload={"status": "GREEN"},
    )
    first_enqueue = outbox.enqueue(event)
    second_enqueue = outbox.enqueue(event)
    delivered: list[str] = []
    outbox.deliver({"CRM": lambda emitted: delivered.append(emitted.event_id)})
    outbox.deliver({"CRM": lambda emitted: delivered.append(emitted.event_id)})
    checks["idempotency"] = first_enqueue and not second_enqueue and delivered == ["EVT-E2E-001"]

    return E2EValidationResult(
        checks=checks,
        representative_domains=coverage,
        representative_cases=len(representative),
    )
