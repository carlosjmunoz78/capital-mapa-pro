import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from jobs.continuous_improvement_runner import CompanyImprovementJob, ImprovementEvidenceContext, ImprovementRunner
from jobs.continuous_improvement_schedule import ScheduleState, default_schedule
from learning.continuous_improvement_runtime import StageResult
from observability.improvement_audit_store import ImprovementAuditStore
from observability.improvement_cycle_summary import summarize_cycle, supervisor_status


class ObservabilitySupervisorTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)

    def test_green_cycle_has_old_new_rollback_and_cost(self):
        job = CompanyImprovementJob(default_schedule("aion", "AUTONOMOUS_VENTURE"), ScheduleState())
        with tempfile.TemporaryDirectory() as td:
            audit = ImprovementAuditStore(Path(td) / "audit.db")
            ctx = ImprovementEvidenceContext("old://v1", "new://v2", "rollback://v1", 0.25)
            ImprovementRunner().execute_due(
                job, self.now, lambda s, a: StageResult(s, "GREEN", f"e://{s}"),
                audit_store=audit, cycle_id="cycle-1", evidence_context=ctx,
            )
            summary = summarize_cycle(audit, company_id="aion", environment="LAB", cycle_id="cycle-1")
            self.assertEqual(summary.status, "GREEN")
            self.assertEqual(summary.stage_count, 12)
            self.assertEqual(summary.total_cost_eur, 3.0)
            self.assertEqual(summary.old_ref, "old://v1")
            self.assertEqual(summary.new_ref, "new://v2")
            self.assertEqual(summary.rollback_ref, "rollback://v1")
            self.assertEqual(supervisor_status(summary)["status"], "GREEN")
            audit.close()

    def test_green_without_promotion_refs_blocks_supervisor(self):
        job = CompanyImprovementJob(default_schedule("aion", "AUTONOMOUS_VENTURE"), ScheduleState())
        with tempfile.TemporaryDirectory() as td:
            audit = ImprovementAuditStore(Path(td) / "audit.db")
            ImprovementRunner().execute_due(
                job, self.now, lambda s, a: StageResult(s, "GREEN", f"e://{s}"),
                audit_store=audit, cycle_id="cycle-2",
            )
            summary = summarize_cycle(audit, company_id="aion", environment="LAB", cycle_id="cycle-2")
            self.assertEqual(summary.status, "GREEN")
            self.assertEqual(supervisor_status(summary)["status"], "BLOCKED")
            audit.close()

    def test_tampered_chain_becomes_security_incident(self):
        job = CompanyImprovementJob(default_schedule("aion", "AUTONOMOUS_VENTURE"), ScheduleState())
        with tempfile.TemporaryDirectory() as td:
            audit = ImprovementAuditStore(Path(td) / "audit.db")
            ImprovementRunner().execute_due(
                job, self.now, lambda s, a: StageResult(s, "GREEN", f"e://{s}"),
                audit_store=audit, cycle_id="cycle-3",
                evidence_context=ImprovementEvidenceContext("old://v1", "new://v2", "rollback://v1"),
            )
            audit.conn.execute("UPDATE improvement_audit SET payload_json='{}' WHERE seq=1")
            audit.conn.commit()
            summary = summarize_cycle(audit, company_id="aion", environment="LAB", cycle_id="cycle-3")
            self.assertEqual(summary.status, "TAMPERED")
            self.assertEqual(supervisor_status(summary), {"status": "HUMAN_REQUIRED", "reason": "SECURITY_INCIDENT"})
            audit.close()

    def test_negative_evidence_cost_fails_closed(self):
        with self.assertRaises(ValueError):
            ImprovementEvidenceContext(cost_eur=-1).validate()


if __name__ == "__main__":
    unittest.main()
