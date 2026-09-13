import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
sys.path.insert(0, str(RUNTIME))

from sqlite_store import SQLiteRuntimeStore
from execution_log import ExecutionLogStore
from dispatcher import DispatchCandidate, classify_candidate, summarize_query


class CoreLogsDispatcherLiveReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        self.tmp.close()
        self.store = SQLiteRuntimeStore(self.tmp.name)

    def tearDown(self):
        self.store.close()
        pathlib.Path(self.tmp.name).unlink(missing_ok=True)

    def test_make_9527162_start_final_semantics_and_same_run_id(self):
        logs = ExecutionLogStore(self.store)
        common = dict(
            company_id="fenix_capital",
            engine_id="core-execution-log",
            scenario_id="9527162",
            operation_type="LEGACY_REPLAY",
            external_id="legacy-fixture-001",
            run_id="RUN-9527162-001",
            message="legacy semantic replay",
            environment="LAB",
            version="1.0.0",
        )
        start = logs.start(**common)
        final = logs.finish(status="OK", **common)
        self.assertEqual(start.status, "STARTED")
        self.assertEqual(final.status, "OK")
        self.assertEqual(start.run_id, final.run_id)
        records = self.store.list_for_company("fenix_capital")
        self.assertEqual(len(records), 2)
        self.assertEqual({r["payload"]["phase"] for r in records}, {"start", "final"})

    def test_make_9537817_query_and_eligible_candidate_semantics(self):
        # Legacy Make used environment label GLOBAL. Shared runtime normalizes that
        # logical scope into LAB/PREPROD/PROD; replay uses LAB and compares behavior.
        query = summarize_query(
            1,
            company_id="fenix_capital",
            engine_id="core-dispatcher",
            environment="LAB",
            version="1.0.0",
        )
        self.assertEqual(query["status"], "CANDIDATES_CLASSIFIED_NO_EXECUTION")
        self.assertEqual(query["platform_state"], "NO_PLATFORM_CALLED")
        self.assertFalse(query["external_action_allowed"])

        candidate = DispatchCandidate(
            company_id="fenix_capital",
            engine_id="core-dispatcher",
            environment="LAB",
            version="1.0.0",
            notion_record_id="fixture-notion-001",
            run_id="RUN-9537817-001",
            platform="FACEBOOK",
            technical_format="IMAGE",
            publication_state="Pendiente de publicar",
            integration_blocked=False,
            has_programming_relation=True,
            has_production_order=True,
            t48_approved=True,
            t48_approval_date_present=True,
            t48_locked_version_present=True,
            t48_hash_present=True,
            real_publication_authorization="NOT_AUTHORIZED",
        )
        result = classify_candidate(candidate)
        self.assertEqual(result["status"], "ROUTE_PREPARED_ENGINE_OFF")
        self.assertEqual(result["platform_state"], "NOT_CALLED")
        self.assertTrue(result["requires_human"])
        self.assertFalse(result["external_action_allowed"])


if __name__ == "__main__":
    unittest.main()
