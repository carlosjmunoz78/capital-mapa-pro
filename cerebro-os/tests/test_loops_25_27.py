import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


pipeline = load("family_pipeline_25_27", "processes/family_pipeline.py")
families = load("families_25_27", "processes/families.py")
grouped = load("grouped_controller_25_27", "processes/grouped_controller.py")


class Loops25To27Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads((ROOT / "registry/canonical_177.json").read_text(encoding="utf-8"))
        cls.canonical = set(data["engine_ids"])

    def test_ten_families_are_unique_and_canonical(self):
        self.assertEqual(10, len(families.PROCESS_FAMILIES))
        families.validate_against_canonical(self.canonical)
        ids = families.all_engine_ids()
        self.assertEqual(len(ids), len(set(ids)))

    def test_each_family_can_close_green_with_evidence(self):
        for family, sequence in families.PROCESS_FAMILIES.items():
            proc = pipeline.OrderedFamilyPipeline("fenix", sequence)
            self.assertEqual(sequence[0], proc.next_engine())
            for engine_id in sequence:
                self.assertTrue(proc.can_advance(engine_id), msg=f"{family}:{engine_id}")
                proc.update(pipeline.ProcessStep("fenix", engine_id, "GREEN", f"evidence:{family}:{engine_id}"))
            self.assertEqual("GREEN", proc.status())
            self.assertIsNone(proc.next_engine())

    def test_dependencies_block_out_of_order_green(self):
        sequence = families.PROCESS_FAMILIES["property_registry"]
        proc = pipeline.OrderedFamilyPipeline("fenix", sequence)
        with self.assertRaises(ValueError):
            proc.update(pipeline.ProcessStep("fenix", "CAT-001", "GREEN", "evidence:cat"))

    def test_cross_company_is_denied(self):
        proc = pipeline.OrderedFamilyPipeline("fenix", families.PROCESS_FAMILIES["notifications"])
        with self.assertRaises(ValueError):
            proc.update(pipeline.ProcessStep("other", "NOTIF-001", "GREEN", "evidence:x"))

    def test_human_required_only_uses_canonical_reasons(self):
        proc = pipeline.OrderedFamilyPipeline("fenix", families.PROCESS_FAMILIES["payments_sla_blocks"])
        proc.update(pipeline.ProcessStep("fenix", "PAY-001", "HUMAN_REQUIRED", human_reason="MONEY_LIMIT"))
        self.assertEqual("HUMAN_REQUIRED", proc.status())
        with self.assertRaises(ValueError):
            proc.update(pipeline.ProcessStep("fenix", "PAY-001", "HUMAN_REQUIRED", human_reason="UNKNOWN_REASON"))

    def test_macro_controller_connects_three_loops(self):
        ctl = grouped.GroupedProcessController(company_id="fenix", environment="LAB")
        self.assertEqual("LOOP-25-COMMS", ctl.next_macro())
        for macro in grouped.MACRO_ORDER:
            for family in grouped.MACRO_LOOPS[macro]:
                ctl.update_family(family, "GREEN", evidence_refs=(f"evidence:{macro}:{family}",))
            self.assertEqual("GREEN", ctl.macro_status(macro))
        self.assertEqual("GREEN", ctl.system_status())
        self.assertIsNone(ctl.next_macro())


if __name__ == "__main__":
    unittest.main()
