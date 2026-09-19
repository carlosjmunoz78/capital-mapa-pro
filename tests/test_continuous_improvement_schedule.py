import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from jobs.continuous_improvement_schedule import ImprovementSchedule, ScheduleState, default_schedule, due, finish, start


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
        self.schedule = default_schedule("aion", "AUTONOMOUS_VENTURE")

    def test_new_company_is_due_immediately(self):
        self.assertTrue(due(self.schedule, ScheduleState(), self.now))

    def test_default_is_daily(self):
        self.assertEqual(self.schedule.interval_hours, 24)
        self.assertTrue(self.schedule.enabled)

    def test_running_job_cannot_overlap(self):
        state = ScheduleState(last_started_at=self.now, running=True)
        self.assertFalse(due(self.schedule, state, self.now + timedelta(days=2)))

    def test_not_due_before_interval(self):
        state = ScheduleState(last_started_at=self.now)
        self.assertFalse(due(self.schedule, state, self.now + timedelta(hours=23, minutes=59)))

    def test_due_at_interval(self):
        state = ScheduleState(last_started_at=self.now)
        self.assertTrue(due(self.schedule, state, self.now + timedelta(hours=24)))

    def test_start_and_finish(self):
        state = start(self.schedule, ScheduleState(), self.now)
        self.assertTrue(state.running)
        state = finish(state, self.now + timedelta(minutes=2))
        self.assertFalse(state.running)
        self.assertEqual(state.last_finished_at, self.now + timedelta(minutes=2))

    def test_disabled_schedule_never_due(self):
        schedule = ImprovementSchedule("aion", "AUTONOMOUS_VENTURE", enabled=False)
        self.assertFalse(due(schedule, ScheduleState(), self.now))

    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            due(self.schedule, ScheduleState(), datetime(2026, 9, 19, 12, 0))


if __name__ == "__main__":
    unittest.main()
