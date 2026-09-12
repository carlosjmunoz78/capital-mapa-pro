import os
import sys
import unittest

HERE = os.path.dirname(__file__)
RUNTIME = os.path.abspath(os.path.join(HERE, "..", "runtime"))
if RUNTIME not in sys.path:
    sys.path.insert(0, RUNTIME)

from core_migration_replay import ReplayCase, compare_old_new


class CoreMigrationReplayTests(unittest.TestCase):
    def test_equivalent_runtime_is_cutover_candidate_without_external_mutation(self):
        cases = (
            ReplayCase("router-text", {"format": "texto"}, {"route": "TEXT"}),
            ReplayCase("router-image", {"format": "imagen"}, {"route": "IMAGE"}),
        )

        def runtime(payload):
            return {"route": "TEXT" if payload["format"] == "texto" else "IMAGE"}

        out = compare_old_new(
            company_id="fenix",
            engine_id="core-router",
            environment="LAB",
            version="1.0.0",
            cases=cases,
            new_runtime=runtime,
        )
        self.assertEqual(out["status"], "GREEN_CODE_CI")
        self.assertTrue(out["cutover_allowed"])
        self.assertTrue(out["old_preserved"])
        self.assertFalse(out["delete_old_allowed"])
        self.assertFalse(out["external_mutation_allowed"])
        self.assertEqual(out["cases_green"], 2)

    def test_mismatch_fails_closed(self):
        cases = (ReplayCase("idempotency", {"key": "a"}, {"duplicate": False}),)
        out = compare_old_new(
            company_id="fenix",
            engine_id="core-idempotency",
            environment="PREPROD",
            version="1.0.0",
            cases=cases,
            new_runtime=lambda payload: {"duplicate": True},
        )
        self.assertEqual(out["status"], "PARITY_RED")
        self.assertFalse(out["cutover_allowed"])
        self.assertEqual(len(out["mismatches"]), 1)

    def test_prod_replay_is_rejected(self):
        with self.assertRaises(ValueError):
            compare_old_new(
                company_id="fenix",
                engine_id="core-router",
                environment="PROD",
                version="1.0.0",
                cases=(ReplayCase("x", {"x": 1}, {"x": 1}),),
                new_runtime=lambda payload: payload,
            )


if __name__ == "__main__":
    unittest.main()
