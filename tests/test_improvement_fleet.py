import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from jobs.continuous_improvement_runner import CompanyImprovementJob, ImprovementEvidenceContext
from jobs.continuous_improvement_schedule import ScheduleState, default_schedule
from jobs.improvement_fleet import FleetJob, ImprovementFleetRunner, supervisor_snapshot
from learning.continuous_improvement_runtime import StageResult


class FleetTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)

    def green_job(self, company):
        job = CompanyImprovementJob(default_schedule(company, "AUTONOMOUS_VENTURE"), ScheduleState())
        return FleetJob(job, lambda s, a: StageResult(s, "GREEN", f"e://{company}/{s}"), ImprovementEvidenceContext("old://1","new://2","rollback://1"))

    def test_ten_companies_run_green(self):
        jobs = tuple(self.green_job(f"company-{i}") for i in range(10))
        result = ImprovementFleetRunner().execute(jobs, self.now)
        self.assertEqual(result.status, "GREEN")
        self.assertEqual(result.green, 10)
        self.assertEqual(supervisor_snapshot(result)["companies"], 10)

    def test_one_failure_does_not_stop_other_companies(self):
        good1 = self.green_job("a")
        bad_job = CompanyImprovementJob(default_schedule("b", "AUTONOMOUS_VENTURE"), ScheduleState())
        bad = FleetJob(bad_job, lambda s, a: (_ for _ in ()).throw(RuntimeError("boom")))
        good2 = self.green_job("c")
        result = ImprovementFleetRunner().execute((good1, bad, good2), self.now)
        self.assertEqual(tuple(o.status for o in result.outcomes), ("GREEN", "BLOCKED", "GREEN"))
        self.assertEqual(result.status, "BLOCKED")

    def test_waiting_isolated_and_visible(self):
        job = CompanyImprovementJob(default_schedule("waiter", "AUTONOMOUS_VENTURE"), ScheduleState())
        def execute(stage, attempt):
            if stage == "TEST":
                return StageResult(stage, "WAITING", "e://wait")
            return StageResult(stage, "GREEN", f"e://{stage}")
        result = ImprovementFleetRunner().execute((FleetJob(job, execute), self.green_job("green")), self.now)
        self.assertEqual(result.waiting, 1)
        self.assertIn("waiter", supervisor_snapshot(result)["attention_company_ids"])

    def test_human_required_has_priority(self):
        job = CompanyImprovementJob(default_schedule("fenix", "FENIX_SENSITIVE"), ScheduleState())
        def execute(stage, attempt):
            if stage == "CANARY":
                return StageResult(stage, "HUMAN_REQUIRED", "e://risk", "HIGH_RISK")
            return StageResult(stage, "GREEN", f"e://{stage}")
        result = ImprovementFleetRunner().execute((FleetJob(job, execute), self.green_job("aion")), self.now)
        self.assertEqual(result.status, "HUMAN_REQUIRED")
        self.assertEqual(result.human_required, 1)

    def test_duplicate_scope_fails_closed(self):
        a = self.green_job("dup")
        with self.assertRaises(ValueError):
            ImprovementFleetRunner().execute((a, a), self.now)

if __name__ == "__main__":
    unittest.main()
