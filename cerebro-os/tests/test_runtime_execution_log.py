import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from execution_log import ExecutionLogEntry, ExecutionLogStore
from sqlite_store import SQLiteRuntimeStore


class RuntimeExecutionLogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = SQLiteRuntimeStore(Path(self.tmp.name) / "runtime.sqlite")
        self.logs = ExecutionLogStore(self.store)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def base(self, **overrides):
        data = dict(
            company_id="fenix-capital",
            engine_id="CORE-LOGS-UNIVERSAL-V1",
            scenario_id="CORE-LOGS-UNIVERSAL-V1",
            operation_type="analytics_capture",
            external_id="654319477768791_122188435538900467",
            run_id="RUN-001",
            message="trace",
            environment="LAB",
            version="1.0.0",
            network="Facebook",
            automatic_action="trace",
            notion_record_id="6682f2f2-7cff-4df7-a6e3-ed69329d020a",
        )
        data.update(overrides)
        return data

    def test_start_and_final_are_persisted_with_same_run_id(self):
        self.logs.start(**self.base())
        self.logs.finish(status="OK", **self.base(message="done"))
        rows = self.store.list_for_company("fenix-capital")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["payload"]["phase"], "start")
        self.assertEqual(rows[1]["payload"]["phase"], "final")
        self.assertEqual(rows[0]["payload"]["run_id"], rows[1]["payload"]["run_id"])

    def test_duplicate_phase_is_blocked(self):
        self.logs.start(**self.base())
        with self.assertRaises(ValueError):
            self.logs.start(**self.base())

    def test_scope_isolated(self):
        self.logs.start(**self.base())
        self.logs.start(**self.base(company_id="other-company"))
        self.logs.start(**self.base(environment="PROD"))
        self.logs.start(**self.base(version="2.0.0"))
        self.assertEqual(len(self.store.list_for_company("fenix-capital")), 3)
        self.assertEqual(len(self.store.list_for_company("other-company")), 1)

    def test_invalid_environment_phase_and_attempts_rejected(self):
        with self.assertRaises(ValueError):
            ExecutionLogEntry(phase="start", status="STARTED", **self.base(environment="DEV")).validate()
        with self.assertRaises(ValueError):
            ExecutionLogEntry(phase="middle", status="OK", **self.base()).validate()
        with self.assertRaises(ValueError):
            ExecutionLogEntry(phase="start", status="STARTED", **self.base(attempts=-1)).validate()

    def test_requires_full_identity(self):
        with self.assertRaises(ValueError):
            ExecutionLogEntry(phase="start", status="STARTED", **self.base(company_id="")).validate()
        with self.assertRaises(ValueError):
            ExecutionLogEntry(phase="start", status="STARTED", **self.base(run_id="")).validate()


if __name__ == "__main__":
    unittest.main()
