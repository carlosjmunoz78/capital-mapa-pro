import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "factory"))
from factory import validate_engine_id
import mass_scaffold as mod


class MassScaffoldCP67(unittest.TestCase):
    def test_invalid_tail_is_preflighted_before_writes(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                mod.generate_all(Path(td), ["AAA-111", "../WRONG"])
            self.assertFalse((Path(td) / "engines" / "AAA-111").exists())

    def test_case_insensitive_duplicates_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "duplicate engine_id"):
                mod.generate_all(Path(td), ["abc-001", "ABC-001"])
            self.assertFalse((Path(td) / "engines" / "ABC-001").exists())

    def test_manifest_and_media_id_agree_on_validation(self):
        for bad in ["A", "-ABC", "12-ABC", "A" * 65, "../AAA", " ", None]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_engine_id(bad)
        self.assertEqual(validate_engine_id(" abc-001 "), "ABC-001")

    def test_plan_outputs_canonical_ids(self):
        plan = mod.MassScaffoldPlan([mod.EngineSpec("abc-001", "ABC")])
        self.assertEqual(plan.output_paths("gen"), ["gen/ABC-001"])
        with self.assertRaises(ValueError):
            mod.MassScaffoldPlan([mod.EngineSpec("abc-001", "a"), mod.EngineSpec("ABC-001", "b")]).validate()

    def test_preexisting_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = root / "engines" / "ABC-002"
            old.mkdir(parents=True)
            (old / "KEEP.txt").write_text("persist")
            with self.assertRaises(FileExistsError):
                mod.generate_all(root, ["ABC-001", "ABC-002"])
            self.assertEqual((old / "KEEP.txt").read_text(), "persist")
            self.assertFalse((root / "engines" / "ABC-001").exists())

    def test_mid_scaffold_failure_removes_only_new(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = root / "engines" / "KEEP-01"
            old.mkdir(parents=True)
            (old / "KEEP.txt").write_text("immutable")
            def stub(r, engine_id, _):
                d = r / "engines" / engine_id
                d.mkdir()
                (d / "config.json").write_text(engine_id)
                if engine_id == "BAD-002":
                    raise RuntimeError("synthetic hook failure")
                return d
            with patch.object(mod, "_load_factory", return_value=SimpleNamespace(validate_engine_id=validate_engine_id, scaffold=stub)):
                with self.assertRaisesRegex(RuntimeError, "synthetic hook failure"):
                    mod.generate_all(root, ["OKA-001", "BAD-002"])
            self.assertEqual((old / "KEEP.txt").read_text(), "immutable")
            self.assertFalse((root / "engines" / "OKA-001").exists())
            self.assertFalse((root / "engines" / "BAD-002").exists())
            self.assertFalse((root / "engines" / ".fact001-mass-scaffold.lock").exists())

    def test_existing_lock_not_stolen(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            eng = root / "engines"
            eng.mkdir()
            (eng / ".fact001-mass-scaffold.lock").write_text("other-run")
            with self.assertRaisesRegex(RuntimeError, "MASS_SCAFFOLD_ALREADY_RUNNING"):
                mod.generate_all(root, ["ABC-001"])
            self.assertEqual((eng / ".fact001-mass-scaffold.lock").read_text(), "other-run")

    def test_unsafe_remote_dispatch_rejected_prewrite(self):
        with tempfile.TemporaryDirectory() as td:
            vals = {k:"secret" for k in ("CEREBRO_FACT_ENROLL_EVENT_KEY","CEREBRO_CLOUDFLARE_API_TOKEN", "CEREBRO_CLOUDFLARE_ACCOUNT_ID", "CEREBRO_FACT_ENROLL_QUEUE_ID")}
            vals["CEREBRO_COMPANY_ID"]="fenix"
            with patch.dict(os.environ, vals):
                with self.assertRaisesRegex(ValueError, "BATCH_REMOTE_ENROLLMENT"):
                    mod.generate_all(Path(td), ["ABC-001"])
            self.assertFalse((Path(td)/"engines"/"ABC-001").exists())

    def test_symlink_engines_folder_rejected(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as ext:
            root=Path(td)
            (root / "engines").symlink_to(ext, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "ENGINES_SYMLINK_DENIED"):
                mod.generate_all(root, ["ABC-001"])
            self.assertEqual(list(Path(ext).iterdir()), [])

    def test_empty_batch_is_noop(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(mod.generate_all(Path(td), []), [])
            self.assertFalse((Path(td) / "engines").exists())

    def test_real_batch_writes_scaffolds_and_releases_lock(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with patch.dict(os.environ, {"CEREBRO_COMPANY_ID":""}):
                paths=mod.generate_all(root, ["aBC-001", "ABC-002"])
            self.assertEqual([p.name for p in paths], ["ABC-001", "ABC-002"])
            for p in paths:
                self.assertTrue((p / "manifest.json").is_file())
                self.assertTrue((p / "events" / "UMS001_FACTORY_ENROLLMENT_STATUS.json").is_file())
            self.assertFalse((root/"engines"/".fact001-mass-scaffold.lock").exists())
            with self.assertRaises(FileExistsError):
                mod.generate_all(root, ["ABC-001"])
            self.assertTrue((paths[0]/"manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()