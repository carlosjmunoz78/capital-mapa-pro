import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from router import DeterministicRouter, RouteDecision
from sqlite_store import SQLiteRuntimeStore


class RuntimeRouterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = SQLiteRuntimeStore(Path(self.tmp.name) / "runtime.sqlite")
        self.router = DeterministicRouter(self.store)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def decision(self, **overrides):
        data = dict(
            company_id="fenix-capital",
            engine_id="CORE-ROUTER-MASTER-V1",
            route_id="FACEBOOK_ANALYTICS_TEST:654319477768791_122188435538900467",
            operation_type="analytics_capture",
            external_id="654319477768791_122188435538900467",
            destination="FACEBOOK_ANALYTICS_TEST",
            status="ROUTED_TO_FACEBOOK_ANALYTICS_TEST",
            message="Orden TEST validada y dirigida al adaptador de analítica Facebook.",
            environment="LAB",
            version="1.0.0",
            network="Facebook",
            run_id="RUN-001",
        )
        data.update(overrides)
        return RouteDecision(**data)

    def test_emits_decision_without_external_action(self):
        result = self.router.emit(self.decision())
        self.assertTrue(result["emitted"])
        self.assertEqual(result["status"], "ROUTED_TO_FACEBOOK_ANALYTICS_TEST")
        self.assertFalse(result["external_action_executed"])
        self.assertEqual(result["destination"], "FACEBOOK_ANALYTICS_TEST")

    def test_duplicate_route_is_blocked(self):
        self.assertTrue(self.router.emit(self.decision())["emitted"])
        duplicate = self.router.emit(self.decision(run_id="RUN-002"))
        self.assertFalse(duplicate["emitted"])
        self.assertEqual(duplicate["status"], "DUPLICATE_ROUTE_BLOCKED")

    def test_scope_isolated(self):
        self.assertTrue(self.router.emit(self.decision())["emitted"])
        self.assertTrue(self.router.emit(self.decision(company_id="other-company"))["emitted"])
        self.assertTrue(self.router.emit(self.decision(environment="PROD"))["emitted"])
        self.assertTrue(self.router.emit(self.decision(version="2.0.0"))["emitted"])

    def test_router_cannot_execute_external_action(self):
        with self.assertRaises(ValueError):
            self.router.emit(self.decision(automatic_action="PUBLISH_TO_FACEBOOK"))

    def test_invalid_scope_and_identity_rejected(self):
        with self.assertRaises(ValueError):
            self.router.emit(self.decision(environment="DEV"))
        with self.assertRaises(ValueError):
            self.router.emit(self.decision(company_id=""))
        with self.assertRaises(ValueError):
            self.router.emit(self.decision(destination=""))

    def test_payload_is_persisted_as_router_decision(self):
        self.router.emit(self.decision())
        rows = self.store.list_for_company("fenix-capital")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["kind"], "router_decision")
        self.assertEqual(rows[0]["payload"]["phase"], "routing")
        self.assertEqual(rows[0]["payload"]["operation_type"], "analytics_capture")
        self.assertFalse(rows[0]["payload"]["requires_human"])


if __name__ == "__main__":
    unittest.main()
