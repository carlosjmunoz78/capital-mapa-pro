import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.case_context import CaseSnapshot
from advisory.integration_events import AdvisoryIntegrationEvent, IntegrationOutbox
from advisory.models import CANONICAL_HUMAN_EXCEPTIONS
from advisory.observability import ExecutionTelemetry, TelemetryCollector, advisory_health
from advisory.recovery import create_backup, rebuild_case_store, rollback_target


class AdvisoryBlockCTests(unittest.TestCase):
    def make_event(self, **overrides):
        values = {
            "event_id": "EVT-001",
            "idempotency_key": "COMPANY-001:CASE-001:CRM:UPDATED",
            "correlation_id": "CORR-001",
            "company_id": "COMPANY-001",
            "case_id": "CASE-001",
            "target": "CRM",
            "event_type": "ADVISORY_CASE_UPDATED",
            "payload": {"status": "GREEN"},
        }
        values.update(overrides)
        return AdvisoryIntegrationEvent(**values)

    def test_canonical_human_exception_contract_has_exact_eight_codes(self):
        self.assertEqual(
            CANONICAL_HUMAN_EXCEPTIONS,
            {
                "LEGAL_REQUIRED",
                "SIGNATURE_REQUIRED",
                "LOW_CONFIDENCE",
                "HIGH_RISK",
                "POLICY_CONFLICT",
                "SECURITY_INCIDENT",
                "MONEY_LIMIT",
                "CUSTOMER_HUMAN_REQUEST",
            },
        )

    def test_outbox_is_idempotent_and_requires_injected_adapter(self):
        outbox = IntegrationOutbox()
        event = self.make_event()
        self.assertTrue(outbox.enqueue(event))
        self.assertFalse(outbox.enqueue(event))
        records = outbox.deliver({})
        self.assertEqual(records[0].state, "BLOCKED")
        self.assertEqual(records[0].attempts, 0)
        self.assertIn("missing adapter", records[0].last_error)

    def test_retry_then_delivery_preserves_idempotency(self):
        outbox = IntegrationOutbox()
        event = self.make_event()
        outbox.enqueue(event)
        calls = []

        def flaky_adapter(delivered_event):
            calls.append(delivered_event.event_id)
            if len(calls) == 1:
                raise RuntimeError("temporary failure")

        first = outbox.deliver({"CRM": flaky_adapter}, max_attempts=3)[0]
        self.assertEqual(first.state, "RETRY")
        self.assertEqual(first.attempts, 1)
        second = outbox.deliver({"CRM": flaky_adapter}, max_attempts=3)[0]
        self.assertEqual(second.state, "DELIVERED")
        self.assertEqual(second.attempts, 2)
        third = outbox.deliver({"CRM": flaky_adapter}, max_attempts=3)[0]
        self.assertEqual(third.state, "DELIVERED")
        self.assertEqual(len(calls), 2)

    def test_idempotency_collision_fails_closed(self):
        outbox = IntegrationOutbox()
        outbox.enqueue(self.make_event())
        with self.assertRaises(ValueError):
            outbox.enqueue(self.make_event(event_id="EVT-OTHER"))

    def test_telemetry_collects_latency_errors_confidence_audit_and_cost(self):
        collector = TelemetryCollector()
        collector.emit(
            ExecutionTelemetry(
                correlation_id="CORR-001",
                company_id="COMPANY-001",
                case_id="CASE-001",
                engine_id="TAX-001",
                environment="PREPROD",
                status="GREEN",
                latency_ms=120,
                confidence=0.93,
                audit_refs=("audit://gateway/1",),
                cost_eur=Decimal("0"),
            )
        )
        collector.emit(
            ExecutionTelemetry(
                correlation_id="CORR-002",
                company_id="COMPANY-001",
                case_id="CASE-002",
                engine_id="TAX-001",
                environment="PREPROD",
                status="BLOCKED",
                latency_ms=80,
                confidence=0.40,
                error_code="LOW_CONFIDENCE",
                cost_eur=Decimal("0"),
            )
        )
        metrics = collector.metrics()
        self.assertEqual(metrics["executions"], 2)
        self.assertEqual(metrics["errors"], 1)
        self.assertEqual(metrics["latency_ms_avg"], 100)
        self.assertEqual(metrics["latency_ms_max"], 120)
        self.assertEqual(metrics["cost_eur_total"], "0")
        self.assertEqual(collector.records()[0].structured_log()["correlation_id"], "CORR-001")

    def test_health_and_readiness_are_green_with_canonical_contracts(self):
        health = advisory_health()
        self.assertEqual(health["liveness"], "GREEN")
        self.assertEqual(health["readiness"], "GREEN")
        self.assertEqual(health["execute_permission"], "advisory:execute")
        self.assertEqual(len(health["human_exception_codes"]), 8)

    def test_backup_rebuild_and_rollback_are_deterministic(self):
        snapshot = CaseSnapshot(
            company_id="COMPANY-001",
            case_id="CASE-001",
            environment="PREPROD",
            version="1.0.0",
            facts={"amount": 100},
            internal_document_refs=("DOC-001",),
            source_ids=("SRC-001",),
        )
        bundle = create_backup(
            (snapshot,),
            version="1.0.0",
            rollback_ref="git://cerebro-engine-factory-v0@ffeb04e",
        )
        self.assertEqual(len(bundle.digest()), 64)
        rebuilt = rebuild_case_store(bundle)
        self.assertEqual(rebuilt.recover("COMPANY-001", "CASE-001"), snapshot)
        self.assertEqual(rollback_target(bundle), "git://cerebro-engine-factory-v0@ffeb04e")


if __name__ == "__main__":
    unittest.main()
