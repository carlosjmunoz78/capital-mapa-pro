import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.case_context import CaseSnapshot, CaseStore
from advisory.models import AdvisoryDecision, DomainOpinion
from advisory.professional_output import normalize_professional_output
from advisory.source_policy import SourceAssessment, SourceRecord, assess_sources


class AdvisoryBlockBTests(unittest.TestCase):
    def test_case_store_is_company_scoped_and_recoverable(self):
        store = CaseStore()
        snapshot = CaseSnapshot(
            company_id="COMPANY-001",
            case_id="CASE-001",
            environment="LAB",
            version="1.0.0",
            facts={"amount": 100},
            internal_document_refs=("DOC-001",),
            source_ids=("SRC-001",),
        )
        store.save(snapshot)
        self.assertEqual(store.recover("COMPANY-001", "CASE-001"), snapshot)
        with self.assertRaises(KeyError):
            store.recover("COMPANY-002", "CASE-001")

    def test_case_store_detaches_mutable_facts_on_save_and_recover(self):
        store = CaseStore()
        facts = {"nested": {"amount": 100}}
        snapshot = CaseSnapshot(
            company_id="COMPANY-001",
            case_id="CASE-MUTABLE",
            environment="LAB",
            version="1.0.0",
            facts=facts,
        )
        store.save(snapshot)
        facts["nested"]["amount"] = 999
        first = store.recover("COMPANY-001", "CASE-MUTABLE")
        self.assertEqual(first.facts["nested"]["amount"], 100)
        first.facts["nested"]["amount"] = 777
        second = store.recover("COMPANY-001", "CASE-MUTABLE")
        self.assertEqual(second.facts["nested"]["amount"], 100)

    def test_live_source_validity_jurisdiction_and_confidence(self):
        records = (
            SourceRecord(
                source_id="SRC-LIVE-ES",
                source_type="LIVE_SOURCE",
                locator="https://example.invalid/current",
                jurisdiction="ES",
                checked_at="2026-09-15",
                confidence=0.95,
                valid_from="2026-01-01",
                valid_to="2026-12-31",
            ),
            SourceRecord(
                source_id="SRC-STABLE",
                source_type="STABLE_KNOWLEDGE",
                locator="repo://knowledge/stable",
                jurisdiction="GLOBAL",
                checked_at="2026-09-15",
                confidence=0.90,
            ),
        )
        assessment = assess_sources(
            records,
            required_jurisdiction="ES",
            as_of=date(2026, 9, 15),
            require_live_source=True,
        )
        self.assertEqual(assessment.status, "GREEN")
        self.assertIn("SRC-LIVE-ES", assessment.accepted_source_ids)

    def test_missing_or_outdated_live_source_escalates_low_confidence(self):
        outdated = (
            SourceRecord(
                source_id="SRC-OLD",
                source_type="LIVE_SOURCE",
                locator="https://example.invalid/old",
                jurisdiction="ES",
                checked_at="2025-01-01",
                confidence=0.99,
                valid_to="2025-12-31",
            ),
        )
        assessment = assess_sources(
            outdated,
            required_jurisdiction="ES",
            as_of=date(2026, 9, 15),
            require_live_source=True,
        )
        self.assertEqual(assessment.status, "HUMAN_REQUIRED")
        self.assertEqual(assessment.human_exception, "LOW_CONFIDENCE")

    def test_normalized_output_propagates_source_low_confidence(self):
        decision = AdvisoryDecision(
            case_id="CASE-001",
            domains=("FISCAL",),
            opinions=(
                DomainOpinion(
                    domain="FISCAL",
                    status="GREEN",
                    summary="Base analysis",
                    source_refs=("SRC-STABLE",),
                    risks=("risk-1",),
                    deadlines=("2026-10-01",),
                    next_actions=("action-1",),
                ),
            ),
            overall_status="GREEN",
            audit_refs=("audit://1",),
        )
        assessment = assess_sources(
            (),
            required_jurisdiction="ES",
            as_of=date(2026, 9, 15),
            require_live_source=True,
        )
        output = normalize_professional_output(decision, assessment)
        self.assertEqual(output.overall_status, "HUMAN_REQUIRED")
        self.assertEqual(output.human_required, ("LOW_CONFIDENCE",))
        self.assertEqual(output.risks, ("risk-1",))
        self.assertEqual(output.deadlines, ("2026-10-01",))
        self.assertEqual(output.next_actions, ("action-1",))

    def test_red_and_blocked_statuses_are_not_downgraded_by_human_review(self):
        for severe in ("RED", "BLOCKED"):
            with self.subTest(status=severe):
                decision = AdvisoryDecision(
                    case_id="CASE-SEVERE",
                    domains=("FISCAL",),
                    opinions=(
                        DomainOpinion(
                            domain="FISCAL",
                            status=severe,
                            summary="Severe result",
                            source_refs=("SRC-OK",),
                            human_exception="HIGH_RISK",
                        ),
                    ),
                    overall_status=severe,
                )
                assessment = SourceAssessment(
                    status="GREEN",
                    human_exception=None,
                    accepted_source_ids=("SRC-OK",),
                    reasons=(),
                )
                output = normalize_professional_output(decision, assessment)
                self.assertEqual(output.overall_status, severe)
                self.assertIn("HIGH_RISK", output.human_required)

    def test_unrelated_accepted_source_cannot_replace_opinion_provenance(self):
        decision = AdvisoryDecision(
            case_id="CASE-PROVENANCE",
            domains=("FISCAL",),
            opinions=(
                DomainOpinion(
                    domain="FISCAL",
                    status="GREEN",
                    summary="Analysis tied to its own source",
                    source_refs=("SRC-OPINION",),
                ),
            ),
            overall_status="GREEN",
        )
        assessment = SourceAssessment(
            status="GREEN",
            human_exception=None,
            accepted_source_ids=("SRC-OTHER",),
            reasons=(),
        )
        output = normalize_professional_output(decision, assessment)
        self.assertEqual(output.overall_status, "HUMAN_REQUIRED")
        self.assertEqual(output.human_required, ("LOW_CONFIDENCE",))
        self.assertEqual(output.source_ids, ())


if __name__ == "__main__":
    unittest.main()
