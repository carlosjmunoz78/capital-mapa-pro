import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "facebook_legacy_supersession.py"
spec = importlib.util.spec_from_file_location("facebook_legacy_supersession", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FacebookLegacySupersessionTests(unittest.TestCase):
    def test_known_legacy_scenarios_are_registered(self):
        self.assertEqual(module.get_supersession(9530582).replacement_scenario_id, 9531078)
        self.assertEqual(module.get_supersession(9528450).replacement_scenario_id, 9530484)
        self.assertEqual(module.get_supersession(9532848).replacement_scenario_id, 9533424)

    def test_old_and_new_are_fail_closed(self):
        for scenario_id in (9530582, 9528450, 9532848):
            item = module.get_supersession(scenario_id)
            self.assertFalse(item.old_external_action_allowed)
            self.assertFalse(item.replacement_external_action_allowed)

    def test_retirement_requires_all_gates(self):
        for missing in ("caller", "replay", "rollback", "live"):
            kwargs = dict(
                scenario_id=9530582,
                caller_map_complete=True,
                replay_parity_green=True,
                rollback_proven=True,
                target_runtime_live=True,
            )
            if missing == "caller": kwargs["caller_map_complete"] = False
            if missing == "replay": kwargs["replay_parity_green"] = False
            if missing == "rollback": kwargs["rollback_proven"] = False
            if missing == "live": kwargs["target_runtime_live"] = False
            self.assertFalse(module.can_retire_legacy(**kwargs))

        self.assertTrue(module.can_retire_legacy(
            scenario_id=9530582,
            caller_map_complete=True,
            replay_parity_green=True,
            rollback_proven=True,
            target_runtime_live=True,
        ))

    def test_unknown_scenario_rejected(self):
        with self.assertRaises(ValueError):
            module.get_supersession(9999999)


if __name__ == "__main__":
    unittest.main()
