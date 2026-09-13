import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_chat_wrapper_lab_20260913.py"
spec = importlib.util.spec_from_file_location("chat_wrapper_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ChatWrapperLabTests(unittest.TestCase):
    def test_chat_family_semantic_replay_is_green_in_lab_only(self):
        result = module.replay()
        self.assertEqual(result["target_count"], 5)
        self.assertEqual(result["fixture_count"], 7)
        self.assertTrue(result["all_fixture_semantics_match"])
        self.assertTrue(result["lab_chat_semantic_replay_green"])
        self.assertFalse(result["rollback_path_proven"])
        self.assertFalse(result["prod_parity_green"])
        self.assertFalse(result["prod_mutation_allowed"])
        self.assertFalse(result["grant_change_allowed"])
        self.assertFalse(result["legacy_retirement_allowed"])

    def test_live_contract_boundaries_are_preserved(self):
        self.assertEqual(
            module.attachment_decision(actor_present=True, message_owned=True, member=True, storage_owned=True, size_bytes=20 * 1024 * 1024, mime_type="application/pdf", v2=False),
            (201, "attachment_created"),
        )
        self.assertEqual(
            module.attachment_decision(actor_present=True, message_owned=True, member=True, storage_owned=False, size_bytes=1, mime_type="application/pdf", v2=False),
            (400, "invalid_storage_path"),
        )
        self.assertEqual(
            module.send_v2_decision(actor_present=True, member=True, body=""),
            (400, "invalid_body"),
        )
        self.assertEqual(
            module.conversation_decision(actor_present=True, valid_members=True, member_count=1, group=False),
            (400, "select_at_least_one_person"),
        )


if __name__ == "__main__":
    unittest.main()
