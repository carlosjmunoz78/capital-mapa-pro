import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from jobs.continuous_improvement_runner import CompanyImprovementJob, ImprovementRunner
from jobs.continuous_improvement_schedule import ScheduleState, default_schedule
from learning.continuous_improvement_runtime import StageResult


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
        self.job = CompanyImprovementJob(default_schedule("aion", "AUTONOMOUS_VENTURE"), ScheduleState())

    def test_due_job_runs_full_cycle(self):
        out = ImprovementRunner().execute_due(self.job, self.now, lambda s, a: StageResult(s, "GREEN", f"e://{s}"))
        self.assertEqual(out.status, "GREEN")
        self.assertFalse(out.state.running)

    def test_not_due_is_noop(self):
        state = ScheduleState(last_started_at=self.now)
        job = CompanyImprovementJob(self.job.schedule, state)
        out = ImprovementRunner().execute_due(job, self.now, lambda s, a: StageResult(s, "GREEN", "e://x"))
        self.assertEqual(out.status, "NOT_DUE")
        self.assertIsNone(out.runtime)

    def test_waiting_preserves_running_state(self):
        def execute(stage, attempt):
            if stage == "TEST":
                return StageResult(stage, "WAITING", "e://wait")
            return StageResult(stage, "GREEN", f"e://{stage}")
        out = ImprovementRunner().execute_due(self.job, self.now, execute)
        self.assertEqual(out.status, "WAITING")
        self.assertTrue(out.state.running)

    def test_red_then_green_is_corrected_in_same_run(self):
        def execute(stage, attempt):
            if stage == "EVALUATE" and attempt == 1:
                return StageResult(stage, "RED", "e://red")
            return StageResult(stage, "GREEN", f"e://{stage}/{attempt}")
        out = ImprovementRunner().execute_due(self.job, self.now, execute)
        self.assertEqual(out.status, "GREEN")

if __name__ == "__main__":
    unittest.main()
