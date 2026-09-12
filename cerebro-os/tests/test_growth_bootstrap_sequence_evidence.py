import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

bootstrap = load("growth_bootstrap_sequence", "growth/bootstrap.py")


class GrowthBootstrapSequenceTests(unittest.TestCase):
    def test_green_requires_order_and_evidence(self):
        state = bootstrap.GrowthBootstrap("fenix", "LAB", "2.0.0")
        with self.assertRaises(ValueError):
            state.update(bootstrap.BootstrapStep("fenix", "SOCBOOT-001", "GREEN", "e:social", "LAB", "2.0.0"))
        with self.assertRaises(ValueError):
            state.update(bootstrap.BootstrapStep("fenix", "SEOBOOT-001", "GREEN", None, "LAB", "2.0.0"))
        state.update(bootstrap.BootstrapStep("fenix", "SEOBOOT-001", "GREEN", "e:seo", "LAB", "2.0.0"))
        self.assertEqual("SOCBOOT-001", state.next_engine())
        state.update(bootstrap.BootstrapStep("fenix", "SOCBOOT-001", "GREEN", "e:social", "LAB", "2.0.0"))
        self.assertEqual("MKTBOOT-001", state.next_engine())

    def test_cross_scope_and_false_system_green_are_denied(self):
        state = bootstrap.GrowthBootstrap("fenix", "LAB", "2.0.0")
        with self.assertRaises(ValueError):
            state.update(bootstrap.BootstrapStep("other", "SEOBOOT-001", "GREEN", "e", "LAB", "2.0.0"))
        with self.assertRaises(ValueError):
            state.update(bootstrap.BootstrapStep("fenix", "SEOBOOT-001", "GREEN", "e", "PROD", "2.0.0"))
        for engine_id in bootstrap.CANONICAL_GROWTH_SEQUENCE:
            state.update(bootstrap.BootstrapStep("fenix", engine_id, "GREEN", f"e:{engine_id}", "LAB", "2.0.0"))
        self.assertEqual("GREEN", state.system_status())
        self.assertIsNone(state.next_engine())


if __name__ == "__main__":
    unittest.main()
