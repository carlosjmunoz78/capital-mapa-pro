import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from jobs.continuous_improvement_runner import CompanyImprovementJob, ImprovementRunner
from jobs.continuous_improvement_schedule import ScheduleState, default_schedule
from learning.continuous_improvement_runtime import StageResult
from observability.improvement_audit_store import ImprovementAuditStore


class RunnerAuditTests(unittest.TestCase):
    def test_runner_emits_stage_evidence(self):
        now = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
        job = CompanyImprovementJob(default_schedule("aion", "AUTONOMOUS_VENTURE"), ScheduleState())
        with tempfile.TemporaryDirectory() as td:
            audit = ImprovementAuditStore(Path(td) / "audit.db")
            out = ImprovementRunner().execute_due(
                job, now, lambda s, a: StageResult(s, "GREEN", f"e://{s}"),
                audit_store=audit, cycle_id="cycle-42",
            )
            rows = audit.cycle_records(company_id="aion", environment="LAB", cycle_id="cycle-42")
            self.assertEqual(out.status, "GREEN")
            self.assertEqual(len(rows), 12)
            self.assertTrue(all(r["evidence_ref"].startswith("e://") for r in rows))
            self.assertTrue(audit.verify_chain(company_id="aion", environment="LAB"))
            audit.close()

if __name__ == "__main__":
    unittest.main()
