import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from jobs.continuous_improvement_runner import CompanyImprovementJob, ImprovementEvidenceContext
from jobs.continuous_improvement_schedule import default_schedule
from jobs.improvement_fleet import FleetJob, ImprovementFleetRunner
from learning.continuous_improvement_runtime import StageResult
from learning.improvement_checkpoint_store import ImprovementCheckpointStore
from observability.improvement_audit_store import ImprovementAuditStore
from observability.improvement_cycle_summary import summarize_cycle


class DurableFleetTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)

    def test_waiting_company_resumes_from_checkpoint_and_finishes(self):
        from jobs.continuous_improvement_schedule import ScheduleState
        schedule = default_schedule("aion", "AUTONOMOUS_VENTURE")
        with tempfile.TemporaryDirectory() as td:
            checkpoint = ImprovementCheckpointStore(Path(td) / "checkpoint.db")
            audit = ImprovementAuditStore(Path(td) / "audit.db")
            ctx = ImprovementEvidenceContext("old://v1", "new://v2", "rollback://v1", 0.0)

            calls = {"test": 0}
            def wait_once(stage, attempt):
                if stage == "TEST" and calls["test"] == 0:
                    calls["test"] += 1
                    return StageResult(stage, "WAITING", "e://test/wait")
                return StageResult(stage, "GREEN", f"e://{stage}/{attempt}")

            first_job = CompanyImprovementJob(schedule, ScheduleState())
            first = ImprovementFleetRunner().execute((
                FleetJob(first_job, wait_once, ctx, checkpoint, audit, "cycle-1"),
            ), self.now)
            self.assertEqual(first.waiting, 1)

            resumed_job = CompanyImprovementJob(schedule, first.outcomes[0].state)
            second = ImprovementFleetRunner().execute((
                FleetJob(resumed_job, lambda s, a: StageResult(s, "GREEN", f"e://{s}/{a}"), ctx, checkpoint, audit, "cycle-1"),
            ), self.now)
            self.assertEqual(second.status, "GREEN")
            self.assertIsNone(checkpoint.load(company_id="aion", environment="LAB", version="1.0.0"))

            summary = summarize_cycle(audit, company_id="aion", environment="LAB", cycle_id="cycle-1")
            self.assertEqual(summary.status, "GREEN")
            self.assertEqual(summary.stage_count, 12)
            self.assertTrue(summary.chain_verified)
            checkpoint.close()
            audit.close()

    def test_two_companies_keep_separate_durable_stores(self):
        from jobs.continuous_improvement_schedule import ScheduleState
        with tempfile.TemporaryDirectory() as td:
            cpa = ImprovementCheckpointStore(Path(td) / "a.db")
            cpb = ImprovementCheckpointStore(Path(td) / "b.db")
            aua = ImprovementAuditStore(Path(td) / "aa.db")
            aub = ImprovementAuditStore(Path(td) / "ab.db")
            ctx = ImprovementEvidenceContext("old://1", "new://2", "rollback://1")
            jobs = (
                FleetJob(CompanyImprovementJob(default_schedule("a", "AUTONOMOUS_VENTURE"), ScheduleState()), lambda s,a: StageResult(s,"GREEN",f"e://a/{s}"), ctx, cpa, aua, "ca"),
                FleetJob(CompanyImprovementJob(default_schedule("b", "AUTONOMOUS_VENTURE"), ScheduleState()), lambda s,a: StageResult(s,"GREEN",f"e://b/{s}"), ctx, cpb, aub, "cb"),
            )
            result = ImprovementFleetRunner().execute(jobs, self.now)
            self.assertEqual(result.green, 2)
            self.assertEqual(len(aua.cycle_records(company_id="a", environment="LAB", cycle_id="ca")), 12)
            self.assertEqual(len(aub.cycle_records(company_id="b", environment="LAB", cycle_id="cb")), 12)
            self.assertEqual(aua.cycle_records(company_id="b", environment="LAB", cycle_id="cb"), [])
            cpa.close(); cpb.close(); aua.close(); aub.close()

if __name__ == "__main__":
    unittest.main()
