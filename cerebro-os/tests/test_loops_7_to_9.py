import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


canonical = load("l79_canonical", "registry/canonical_loader.py")
live = load("l79_live", "registry/live_status.py")
gaps = load("l79_gaps", "factory/gap_closer.py")
readiness = load("l79_readiness", "registry/readiness_matrix.py")


class LoopsSevenToNineTests(unittest.TestCase):
    def test_loop7_green_state_requires_evidence(self):
        with self.assertRaises(ValueError):
            live.make_status(
                engine_id="FACT-001",
                company_id="fenix-capital",
                environment="LAB",
                version="0.1.0",
                state="LAB_GREEN",
            )
        record = live.make_status(
            engine_id="FACT-001",
            company_id="fenix-capital",
            environment="LAB",
            version="0.1.0",
            state="LAB_GREEN",
            evidence_refs=("ci://run/57",),
        )
        self.assertEqual("LAB_GREEN", record["state"])

    def test_loop8_gap_closer_separates_safe_autofix_from_policy_review(self):
        present = {
            "manifest", "config", "contracts", "events", "jobs", "api", "tests",
            "evaluation", "observability", "cost", "backup", "rollback", "rebuild", "docs", "training_hooks",
        }
        result = gaps.gap_actions("FACT-001", present)
        self.assertFalse(result["complete"])
        self.assertIn("permissions", result["missing"])
        self.assertIn("policies", result["missing"])
        review = {item["requirement"]: item["mode"] for item in result["actions"]}
        self.assertEqual("POLICY_REVIEW", review["permissions"])
        self.assertEqual("POLICY_REVIEW", review["policies"])
        complete = gaps.gap_actions("FACT-001", set(gaps.STANDARD_REQUIREMENTS))
        self.assertTrue(complete["complete"])
        self.assertEqual((), complete["missing"])

    def test_loop9_readiness_matrix_never_fakes_unverified_green(self):
        ids = canonical.canonical_engine_ids()
        records = [
            live.make_status(
                engine_id="FACT-001",
                company_id="fenix-capital",
                environment="LAB",
                version="0.1.0",
                state="LAB_GREEN",
                evidence_refs=("ci://run/57",),
            ),
            live.make_status(
                engine_id="GOV-001",
                company_id="fenix-capital",
                environment="LAB",
                version="0.1.0",
                state="DOCUMENTED_PARTIAL",
            ),
        ]
        matrix = readiness.build_readiness_matrix(canonical_ids=ids, live_records=records)
        self.assertEqual(177, len(matrix))
        by_id = {row["engine_id"]: row for row in matrix}
        self.assertEqual("LAB_GREEN", by_id["FACT-001"]["state"])
        self.assertEqual("DOCUMENTED_PARTIAL", by_id["GOV-001"]["state"])
        self.assertEqual("UNKNOWN_REQUIRES_AUDIT", by_id["CORE-001"]["state"])
        summary = readiness.summarize(matrix)
        self.assertEqual(177, summary["total"])
        self.assertGreater(summary["counts"]["UNKNOWN_REQUIRES_AUDIT"], 0)


if __name__ == "__main__":
    unittest.main()
