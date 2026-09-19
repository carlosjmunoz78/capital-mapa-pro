import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from jobs.continuous_improvement_runner import CompanyImprovementJob, ImprovementRunner
from jobs.continuous_improvement_schedule import ScheduleState, default_schedule
from learning.continuous_improvement_runtime import ContinuousImprovementRuntime, RuntimeSnapshot, StageResult
from learning.improvement_checkpoint_store import ImprovementCheckpointStore


class ResumeTests(unittest.TestCase):
    def test_runtime_restores_at_waiting_stage(self):
        snap = RuntimeSnapshot("aion", "AUTONOMOUS_VENTURE", "LAB", "1.0.0", (
            StageResult("OBSERVE", "GREEN", "e://observe"),
            StageResult("MEASURE", "WAITING", "e://wait"),
        ), "WAITING")
        rt = ContinuousImprovementRuntime.from_snapshot(snap)
        self.assertEqual(rt.next_stage(), "MEASURE")

    def test_runner_resumes_and_clears_green_checkpoint(self):
        now = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as td:
            store = ImprovementCheckpointStore(Path(td) / "state.db")
            store.save(RuntimeSnapshot("aion", "AUTONOMOUS_VENTURE", "LAB", "1.0.0", (
                StageResult("OBSERVE", "GREEN", "e://observe"),
                StageResult("MEASURE", "WAITING", "e://wait"),
            ), "WAITING"))
            job = CompanyImprovementJob(default_schedule("aion", "AUTONOMOUS_VENTURE"), ScheduleState())
            out = ImprovementRunner().execute_due(job, now, lambda s, a: StageResult(s, "GREEN", f"e://{s}"), store)
            self.assertEqual(out.status, "GREEN")
            self.assertIsNone(store.load(company_id="aion", environment="LAB", version="1.0.0"))
            store.close()

    def test_out_of_order_checkpoint_rejected(self):
        snap = RuntimeSnapshot("aion", "AUTONOMOUS_VENTURE", "LAB", "1.0.0", (
            StageResult("MEASURE", "GREEN", "e://bad"),
        ), "IN_PROGRESS")
        with self.assertRaises(ValueError):
            ContinuousImprovementRuntime.from_snapshot(snap)

if __name__ == "__main__":
    unittest.main()
