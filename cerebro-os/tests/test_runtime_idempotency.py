import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from idempotency import IdempotencyClaim, IdempotencyRegistry
from sqlite_store import SQLiteRuntimeStore


class RuntimeIdempotencyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = SQLiteRuntimeStore(Path(self.tmp.name) / "runtime.sqlite")
        self.registry = IdempotencyRegistry(self.store)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def claim(self, **overrides):
        data = dict(
            idempotency_key="FACEBOOK_POST_001",
            company_id="fenix-capital",
            engine_id="CORE-IDEMPOTENCY-V1",
            operation_type="publish_test",
            external_id="FACEBOOK_POST_001",
            environment="LAB",
            version="1.0.0",
            network="Facebook",
            run_id="RUN-001",
        )
        data.update(overrides)
        return IdempotencyClaim(**data)

    def test_first_seen_then_duplicate_blocked(self):
        first = self.registry.claim(self.claim())
        duplicate = self.registry.claim(self.claim(run_id="RUN-002"))
        self.assertTrue(first["allowed"])
        self.assertEqual(first["status"], "FIRST_SEEN")
        self.assertFalse(duplicate["allowed"])
        self.assertEqual(duplicate["status"], "BLOCKED_DUPLICATE")
        self.assertEqual(duplicate["automatic_action"], "BLOCK_FOLLOWING_ACTION")

    def test_scope_isolated_by_company_environment_version_and_engine(self):
        self.assertTrue(self.registry.claim(self.claim())["allowed"])
        self.assertTrue(self.registry.claim(self.claim(company_id="other-company"))["allowed"])
        self.assertTrue(self.registry.claim(self.claim(environment="PROD"))["allowed"])
        self.assertTrue(self.registry.claim(self.claim(version="2.0.0"))["allowed"])
        self.assertTrue(self.registry.claim(self.claim(engine_id="CORE-IDEMPOTENCY-V2"))["allowed"])

    def test_run_id_preserved_when_provided(self):
        result = self.registry.claim(self.claim(run_id="20260912112233444"))
        self.assertEqual(result["run_id"], "20260912112233444")

    def test_run_id_generated_when_missing(self):
        result = self.registry.claim(self.claim(run_id=None))
        self.assertTrue(result["run_id"])
        self.assertGreaterEqual(len(result["run_id"]), 17)

    def test_invalid_scope_is_rejected(self):
        with self.assertRaises(ValueError):
            self.registry.claim(self.claim(environment="DEV"))
        with self.assertRaises(ValueError):
            self.registry.claim(self.claim(company_id=""))
        with self.assertRaises(ValueError):
            self.registry.claim(self.claim(version=""))

    def test_payload_persisted_with_full_scope(self):
        self.registry.claim(self.claim())
        rows = self.store.list_for_company("fenix-capital")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["kind"], "idempotency")
        self.assertEqual(row["engine_id"], "CORE-IDEMPOTENCY-V1")
        self.assertEqual(row["environment"], "LAB")
        self.assertEqual(row["version"], "1.0.0")
        self.assertEqual(row["payload"]["operation_type"], "publish_test")
        self.assertEqual(row["payload"]["external_id"], "FACEBOOK_POST_001")


if __name__ == "__main__":
    unittest.main()
