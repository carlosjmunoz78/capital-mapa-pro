import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
sys.path.insert(0, str(RUNTIME))

from sqlite_store import SQLiteRuntimeStore
from idempotency import IdempotencyClaim, IdempotencyRegistry
from router import DeterministicRouter, RouteDecision


class CoreIdempotencyRouterLiveReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        self.tmp.close()
        self.store = SQLiteRuntimeStore(self.tmp.name)

    def tearDown(self):
        self.store.close()
        pathlib.Path(self.tmp.name).unlink(missing_ok=True)

    def test_make_9524837_semantics_replay_exactly(self):
        registry = IdempotencyRegistry(self.store)
        claim = IdempotencyClaim(
            idempotency_key="IDEMPOTENCY_TEST_FACEBOOK_POST_001",
            company_id="fenix_capital",
            engine_id="core-idempotency",
            operation_type="FACEBOOK_POST",
            external_id="legacy-fixture-001",
            environment="LAB",
            version="1.0.0",
            run_id="RUN-9524837-001",
        )
        first = registry.claim(claim)
        duplicate = registry.claim(claim)
        self.assertEqual(first["status"], "FIRST_SEEN")
        self.assertTrue(first["allowed"])
        self.assertEqual(duplicate["status"], "BLOCKED_DUPLICATE")
        self.assertFalse(duplicate["allowed"])
        self.assertEqual(first["scope"]["company_id"], "fenix_capital")
        self.assertEqual(first["scope"]["environment"], "LAB")

    def test_make_9527140_semantics_replay_exactly_without_external_action(self):
        router = DeterministicRouter(self.store)
        decision = RouteDecision(
            company_id="fenix_capital",
            engine_id="core-router",
            route_id="ROUTE-9527140-001",
            operation_type="FACEBOOK_ANALYTICS_TEST",
            external_id="legacy-fixture-001",
            destination="FACEBOOK_ANALYTICS_TEST",
            status="ROUTED_TO_FACEBOOK_ANALYTICS_TEST",
            message="legacy semantic replay",
            environment="LAB",
            version="1.0.0",
            run_id="RUN-9527140-001",
        )
        result = router.emit(decision)
        self.assertTrue(result["emitted"])
        self.assertEqual(result["status"], "ROUTED_TO_FACEBOOK_ANALYTICS_TEST")
        self.assertEqual(result["destination"], "FACEBOOK_ANALYTICS_TEST")
        self.assertFalse(result["external_action_executed"])


if __name__ == "__main__":
    unittest.main()
