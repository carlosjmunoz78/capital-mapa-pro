import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "core_specific_replay_contracts.py"
spec = importlib.util.spec_from_file_location("core_specific_replay_contracts", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CoreSpecificReplayContractsTests(unittest.TestCase):
    def test_exact_legacy_core_inventory(self):
        self.assertEqual(set(module.LEGACY_CORE_REPLAY), {9524837, 9527140, 9527162, 9537817})

    def test_all_old_contracts_are_non_external(self):
        for item in module.LEGACY_CORE_REPLAY.values():
            self.assertFalse(item["old_external_action"])

    def test_idempotency_contract_preserves_first_seen_and_duplicate(self):
        item = module.get_contract(9524837)
        self.assertEqual(item["runtime"], "idempotency.py")
        self.assertEqual(item["runtime_invariants"]["first_seen_status"], "FIRST_SEEN")
        self.assertEqual(item["runtime_invariants"]["duplicate_status"], "BLOCKED_DUPLICATE")

    def test_router_contract_never_executes_external_action(self):
        item = module.get_contract(9527140)
        self.assertEqual(item["runtime"], "router.py")
        self.assertFalse(item["runtime_invariants"]["external_action_executed"])

    def test_logs_contract_preserves_start_final_and_same_run_id(self):
        item = module.get_contract(9527162)
        self.assertEqual(item["runtime"], "execution_log.py")
        self.assertEqual(item["runtime_invariants"]["phases"], ("start", "final"))
        self.assertTrue(item["runtime_invariants"]["same_run_id_required"])

    def test_dispatcher_contract_preserves_t48_and_no_platform_call(self):
        item = module.get_contract(9537817)
        self.assertEqual(item["runtime"], "dispatcher.py")
        self.assertTrue(item["runtime_invariants"]["t48_required"])
        self.assertFalse(item["runtime_invariants"]["external_action_allowed"])
        self.assertEqual(item["runtime_invariants"]["platform_state"], "NOT_CALLED")

    def test_replay_gate_is_fail_closed_until_all_checks_green(self):
        for missing in ("live_contract_captured", "runtime_present", "replay_fixture_present", "rollback_proven"):
            kwargs = dict(live_contract_captured=True, runtime_present=True, replay_fixture_present=True, rollback_proven=True)
            kwargs[missing] = False
            result = module.replay_readiness(9524837, **kwargs)
            self.assertEqual(result["status"], "PARITY_PENDING")
            self.assertFalse(result["prod_cutover_allowed"])
            self.assertTrue(result["old_preserved"])

    def test_green_code_ci_still_never_allows_prod_cutover_or_delete(self):
        result = module.replay_readiness(
            9537817,
            live_contract_captured=True,
            runtime_present=True,
            replay_fixture_present=True,
            rollback_proven=True,
        )
        self.assertEqual(result["status"], "GREEN_CODE_CI")
        self.assertFalse(result["prod_cutover_allowed"])
        self.assertFalse(result["delete_old_allowed"])
        self.assertFalse(result["external_action_allowed"])

    def test_unknown_scenario_fails_closed(self):
        with self.assertRaises(ValueError):
            module.get_contract(1)


if __name__ == "__main__":
    unittest.main()
