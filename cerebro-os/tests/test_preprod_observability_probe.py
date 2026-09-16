import contextlib
import importlib.util
import io
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "preprod" / "run_candidate.py"
spec = importlib.util.spec_from_file_location("preprod_run_candidate", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PreprodObservabilityProbeTests(unittest.TestCase):
    def test_probe_emits_scoped_log_metric_incident_for_each_advisory_engine(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            module.emit_persistent_observability_probe()

        rows = [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]
        expected_engines = sorted(
            {
                engine_id
                for capability in module.CAPABILITY_REGISTRY.values()
                for engine_id in capability.engine_ids
            }
        )
        self.assertEqual(len(rows), len(expected_engines) * 3)
        self.assertEqual({row["engine_id"] for row in rows}, set(expected_engines))
        self.assertEqual({row["kind"] for row in rows}, {"log", "metric", "incident"})
        self.assertEqual({row["company_id"] for row in rows}, {"fenix-capital"})
        self.assertEqual({row["environment"] for row in rows}, {"PREPROD"})
        self.assertEqual({row["version"] for row in rows}, {"advisory-preprod-v1"})
        self.assertEqual({row["marker"] for row in rows}, {module.OBSERVABILITY_MARKER})
        self.assertTrue(all(row["synthetic"] is True for row in rows))


if __name__ == "__main__":
    unittest.main()
