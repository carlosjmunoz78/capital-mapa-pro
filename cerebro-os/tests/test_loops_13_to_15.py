import importlib.util
import sys
import tempfile
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


evidence = load("l1315_evidence", "registry/evidence_store.py")
controller = load("l1315_controller", "supervisor/loop_controller.py")
system_loop = load("l1315_system", "supervisor/system_loop.py")


class LoopsThirteenToFifteenTests(unittest.TestCase):
    def test_loop13_evidence_store_is_tenant_scoped_and_immutable(self):
        with tempfile.TemporaryDirectory() as td:
            store = evidence.EvidenceStore(Path(td) / "evidence.db")
            eid = store.append(
                company_id="fenix-capital", engine_id="FACT-001", version="0.1.0",
                environment="LAB", kind="CI", reference="ci://run/66", evidence_id="ev-1",
            )
            self.assertEqual("ev-1", eid)
            store.append(
                company_id="other", engine_id="FACT-001", version="0.1.0",
                environment="LAB", kind="CI", reference="ci://run/other", evidence_id="ev-2",
            )
            self.assertEqual(1, len(store.list_engine(company_id="fenix-capital", engine_id="FACT-001")))
            with self.assertRaises(ValueError):
                store.append(
                    company_id="fenix-capital", engine_id="FACT-001", version="0.1.0",
                    environment="LAB", kind="CI", reference="ci://duplicate", evidence_id="ev-1",
                )
            store.close()

    def test_loop14_controller_prioritizes_blocked_and_never_autofixes_policy(self):
        matrix = (
            {"engine_id": "CORE-001", "state": "UNKNOWN_REQUIRES_AUDIT"},
            {"engine_id": "FACT-001", "state": "LAB_GREEN"},
            {"engine_id": "GOV-001", "state": "BLOCKED"},
        )
        selected = controller.select_next_engine(matrix)
        self.assertEqual("GOV-001", selected["engine_id"])
        self.assertEqual("BLOCKED", controller.next_action(selected)["action"])
        plan = controller.gap_plan(
            engine_id="CORE-001",
            missing=("docs", "permissions", "policies"),
            auto_safe={"docs"},
        )
        self.assertEqual(("docs",), plan["safe_autofix"])
        self.assertEqual(("permissions", "policies"), plan["review_required"])

    def test_loop15_state_machine_requires_tests_and_evidence_before_green(self):
        self.assertEqual("AUDIT", system_loop.loop_transition(state="UNKNOWN_REQUIRES_AUDIT")["phase"])
        self.assertEqual(
            "SAFE_AUTOFIX",
            system_loop.loop_transition(state="DEFINED_NOT_BUILT", audit_complete=True, safe_autofix_remaining=("docs",))["phase"],
        )
        self.assertEqual(
            "REVIEW",
            system_loop.loop_transition(state="DEFINED_NOT_BUILT", audit_complete=True, review_required=("permissions",))["phase"],
        )
        self.assertEqual(
            "TEST",
            system_loop.loop_transition(state="DEFINED_NOT_BUILT", audit_complete=True, tests_green=False)["phase"],
        )
        self.assertEqual(
            "EVIDENCE",
            system_loop.loop_transition(state="DEFINED_NOT_BUILT", audit_complete=True, tests_green=True, evidence_present=False)["phase"],
        )
        green = system_loop.loop_transition(state="DEFINED_NOT_BUILT", audit_complete=True, tests_green=True, evidence_present=True)
        self.assertEqual({"phase": "GREEN", "result": "LAB_GREEN"}, green)
        system = system_loop.system_loop_status(canonical_count=177, green_count=176)
        self.assertEqual("RED", system["state"])
        self.assertEqual(1, system["pending"])
        complete = system_loop.system_loop_status(canonical_count=177, green_count=177)
        self.assertEqual("GREEN", complete["state"])


if __name__ == "__main__":
    unittest.main()
