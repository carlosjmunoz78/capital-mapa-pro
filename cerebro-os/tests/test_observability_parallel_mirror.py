import importlib.util
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


mirror = load("observability_parallel_mirror", ROOT / "runtime" / "observability_parallel_mirror.py")
store_module = load("observability_store", ROOT / "runtime" / "observability_store.py")


class ParallelMirrorTests(unittest.TestCase):
    def test_all_legacy_sources_map_to_supported_kinds_and_prod_stays_disabled(self):
        result = mirror.assess_parallel_mirroring()
        self.assertEqual(result["legacy_source_count"], 6)
        self.assertEqual(result["required_scope"], ("company_id", "engine_id", "environment", "version"))
        self.assertFalse(result["legacy_tables_modified"])
        self.assertTrue(result["parallel_auxiliary_sink_only"])
        self.assertTrue(result["lab_mirroring_implementation_ready"])
        self.assertFalse(result["prod_mirroring_enabled"])
        self.assertFalse(result["prod_per_engine_coverage_proven"])
        self.assertFalse(result["additional_subscription_required"])
        self.assertFalse(result["automatic_prod_promotion_allowed"])

    def test_missing_scope_fails_closed(self):
        with self.assertRaises(ValueError):
            mirror.build_parallel_envelope(
                source_table="activity_log",
                scope={"company_id": "fenix", "engine_id": "ENG-1", "environment": "LAB"},
                name="activity",
                payload={},
                evidence_ref="test",
            )

    def test_lab_mirror_writes_only_auxiliary_sqlite_with_full_scope(self):
        envelope = mirror.build_parallel_envelope(
            source_table="activity_log",
            scope={"company_id": "fenix", "engine_id": "ENG-1", "environment": "LAB", "version": "v1"},
            name="activity",
            payload={"action": "sample"},
            evidence_ref="lab-fixture",
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = store_module.SQLiteObservabilityStore(pathlib.Path(tmp) / "obs.sqlite")
            try:
                row_id = mirror.mirror_to_store(store, envelope)
                self.assertGreater(row_id, 0)
                coverage = store.coverage("fenix", "LAB", ["ENG-1"])
                self.assertTrue(coverage["all_required_engines_have_log"])
                self.assertFalse(coverage["all_required_engines_have_metric"])
                self.assertFalse(coverage["all_required_engines_have_incident"])
                self.assertFalse(coverage["additional_subscription_required"])
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
