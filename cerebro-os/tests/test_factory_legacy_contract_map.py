import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "factory_legacy_contract_map.py"
spec = importlib.util.spec_from_file_location("factory_legacy_contract_map", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FactoryLegacyContractMapTests(unittest.TestCase):
    def test_exact_factory_inventory_is_registered(self):
        self.assertEqual(set(module.FACTORY_LEGACY_MAP), {9533982, 9534003, 9534002, 9533999, 9533998, 9533997})

    def test_all_legacy_scenarios_remain_inactive_and_fail_closed(self):
        self.assertTrue(module.all_legacy_fail_closed())
        for scenario_id in module.FACTORY_LEGACY_MAP:
            result = module.assess_factory_migration_readiness(
                scenario_id=scenario_id,
                live_contract_captured=True,
                runtime_target_exists=True,
                replay_parity_green=True,
                rollback_proven=True,
            )
            self.assertTrue(result["green_code_ci"])
            self.assertTrue(result["legacy_must_remain_inactive"])
            self.assertFalse(result["delete_legacy_allowed"])
            self.assertFalse(result["autoactivate_legacy_allowed"])
            self.assertFalse(result["external_action_allowed"])
            self.assertFalse(result["prod_cutover_allowed"])

    def test_provider_adapter_targets_match_captured_make_contracts(self):
        self.assertEqual(module.get_factory_legacy_contract(9534003)["difference"], "VIDEO_EDITOR_API_NOT_CONNECTED")
        self.assertEqual(module.get_factory_legacy_contract(9534002)["difference"], "VIDEO_GENERATOR_API_NOT_CONNECTED")
        self.assertEqual(module.get_factory_legacy_contract(9533999)["difference"], "PRESENTER_API_NOT_CONNECTED")
        self.assertEqual(module.get_factory_legacy_contract(9533998)["difference"], "TTS_API_NOT_CONNECTED")

    def test_image_adapter_is_explicitly_native_migration_and_paid_old_edge_is_not_reused(self):
        item = module.get_factory_legacy_contract(9533997)
        self.assertEqual(item["migration"], "MIGRATE_TO_NATIVE_RUNTIME_KEEP_INACTIVE")
        self.assertTrue(item["paid_provider_present_in_old"])
        self.assertEqual(item["old_provider"], "gpt-image-1")
        self.assertIn("OpenAI image generation", item["old_external_mutations"])
        self.assertFalse(item["old_external_action_allowed"])

    def test_each_missing_gate_blocks_green_code_ci(self):
        for gate in ("live_contract_captured", "runtime_target_exists", "replay_parity_green", "rollback_proven"):
            kwargs = dict(
                scenario_id=9534002,
                live_contract_captured=True,
                runtime_target_exists=True,
                replay_parity_green=True,
                rollback_proven=True,
            )
            kwargs[gate] = False
            result = module.assess_factory_migration_readiness(**kwargs)
            self.assertFalse(result["green_code_ci"])

    def test_unknown_scenario_fails_closed(self):
        with self.assertRaises(ValueError):
            module.get_factory_legacy_contract(1)


if __name__ == "__main__":
    unittest.main()
