import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from learning.continuous_improvement_runtime import ContinuousImprovementRuntime, StageResult


class RuntimeTests(unittest.TestCase):
    def test_all_green_runs_to_completion(self):
        rt = ContinuousImprovementRuntime("aion", "AUTONOMOUS_VENTURE")
        snap = rt.run_until_pause(lambda stage, attempt: StageResult(stage, "GREEN", f"evidence://{stage}/{attempt}"))
        self.assertEqual(snap.status, "GREEN")
        self.assertEqual(len(snap.stage_results), 12)

    def test_red_is_corrected_then_continues(self):
        rt = ContinuousImprovementRuntime("aion", "AUTONOMOUS_VENTURE")
        def execute(stage, attempt):
            if stage == "TEST" and attempt == 1:
                return StageResult(stage, "RED", "evidence://test/red")
            return StageResult(stage, "GREEN", f"evidence://{stage}/{attempt}")
        snap = rt.run_until_pause(execute)
        self.assertEqual(snap.status, "GREEN")
        test = [x for x in snap.stage_results if x.stage == "TEST"][0]
        self.assertEqual(test.status, "GREEN")

    def test_waiting_pauses_without_skipping(self):
        rt = ContinuousImprovementRuntime("aion", "AUTONOMOUS_VENTURE")
        def execute(stage, attempt):
            if stage == "EVALUATE":
                return StageResult(stage, "WAITING", "evidence://pending")
            return StageResult(stage, "GREEN", f"evidence://{stage}")
        snap = rt.run_until_pause(execute)
        self.assertEqual(snap.status, "WAITING")
        self.assertEqual(rt.next_stage(), "EVALUATE")

    def test_repeated_red_blocks_after_bounded_retries(self):
        rt = ContinuousImprovementRuntime("aion", "AUTONOMOUS_VENTURE", max_red_retries=3)
        def execute(stage, attempt):
            if stage == "TRIBUNAL":
                return StageResult(stage, "RED", f"evidence://red/{attempt}")
            return StageResult(stage, "GREEN", f"evidence://{stage}")
        snap = rt.run_until_pause(execute)
        self.assertEqual(snap.status, "BLOCKED")

    def test_human_required_stops_loop(self):
        rt = ContinuousImprovementRuntime("fenix", "FENIX_SENSITIVE")
        def execute(stage, attempt):
            if stage == "CANARY":
                return StageResult(stage, "HUMAN_REQUIRED", "evidence://risk", "HIGH_RISK")
            return StageResult(stage, "GREEN", f"evidence://{stage}")
        snap = rt.run_until_pause(execute)
        self.assertEqual(snap.status, "HUMAN_REQUIRED")
        self.assertIsNone(rt.next_stage())

    def test_green_without_evidence_fails_closed(self):
        rt = ContinuousImprovementRuntime("aion", "AUTONOMOUS_VENTURE")
        with self.assertRaises(ValueError):
            rt.run_once(lambda stage, attempt: StageResult(stage, "GREEN"))

    def test_wrong_stage_result_rejected(self):
        rt = ContinuousImprovementRuntime("aion", "AUTONOMOUS_VENTURE")
        with self.assertRaises(ValueError):
            rt.run_once(lambda stage, attempt: StageResult("WRONG", "GREEN", "evidence://x"))


if __name__ == "__main__":
    unittest.main()
