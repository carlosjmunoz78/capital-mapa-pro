import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "recovery_external_evidence_inventory.py"
spec = importlib.util.spec_from_file_location("recovery_external_evidence_inventory", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RecoveryExternalEvidenceInventoryTests(unittest.TestCase):
    def test_make_preventive_scenarios_do_not_fake_backup_or_restore_proof(self):
        for key in ("make_9527263", "make_9524813"):
            item = module.LIVE_EVIDENCE[key]
            self.assertFalse(item.proves_source_backup)
            self.assertFalse(item.proves_provider_restore)
            self.assertFalse(item.destructive_action_allowed)

    def test_pinned_git_commit_is_source_snapshot_only(self):
        item = module.LIVE_EVIDENCE["github_pinned_source_snapshot"]
        self.assertTrue(item.proves_source_backup)
        self.assertFalse(item.proves_rebuild)
        self.assertFalse(item.proves_provider_restore)
        self.assertIn("e0e5b41e3a05198d015af7bcd0387d4ff3c66e48", item.source)

    def test_ci_rehearsal_is_runtime_only_not_provider_restore(self):
        item = module.LIVE_EVIDENCE["github_ci_runtime_rehearsal"]
        self.assertTrue(item.proves_rebuild)
        self.assertTrue(item.proves_rollback_rehearsal)
        self.assertFalse(item.proves_provider_restore)

    def test_summary_closes_source_recovery_but_not_provider_restore(self):
        summary = module.summarize_recovery_external_evidence()
        self.assertEqual(summary["status"], "EXTERNAL_PROOF_PENDING")
        self.assertTrue(summary["checks"]["source_backup"])
        self.assertTrue(summary["source_recovery_green"])
        self.assertFalse(summary["recovery_green"])
        self.assertFalse(summary["provider_restore_green"])
        self.assertNotIn("source_backup", summary["missing"])
        self.assertEqual(summary["missing"], ("provider_restore",))
        self.assertFalse(summary["destructive_action_allowed"])


if __name__ == "__main__":
    unittest.main()
