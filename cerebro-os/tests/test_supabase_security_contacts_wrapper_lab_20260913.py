import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_contacts_wrapper_lab_20260913.py"
spec = importlib.util.spec_from_file_location("contacts_wrapper_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ContactsWrapperLabTests(unittest.TestCase):
    def test_contacts_family_semantic_replay_is_green_in_lab_only(self):
        result = module.replay()
        self.assertEqual(result["target_count"], 2)
        self.assertEqual(result["fixture_count"], 5)
        self.assertTrue(result["v1_semantic_replay_green"])
        self.assertTrue(result["v2_normalization_replay_green"])
        self.assertTrue(result["lab_contacts_semantic_replay_green"])
        self.assertFalse(result["rollback_path_proven"])
        self.assertFalse(result["prod_parity_green"])
        self.assertFalse(result["prod_mutation_allowed"])
        self.assertFalse(result["grant_change_allowed"])
        self.assertFalse(result["legacy_retirement_allowed"])

    def test_role_entity_and_duplicate_guards_are_preserved(self):
        self.assertEqual(module.create_decision(actor_present=True, role="Visitador", contact_type="trabajador_inmobiliaria", name="Luis", entity_id=None), (400, "entity_required"))
        self.assertEqual(module.create_decision(actor_present=True, role="Visitador", contact_type="trabajador_inmobiliaria", name="Luis", entity_id="i1", entity_visible=False), (403, "entity_not_found_or_forbidden"))
        self.assertEqual(module.create_decision(actor_present=True, role="Financiero", contact_type="contacto_bancario", name="Eva"), (403, "forbidden"))
        self.assertEqual(module.create_decision(actor_present=True, role="Direccion", contact_type="cliente_herencia", name="Eva", duplicate=True), (409, "duplicate_contact"))


if __name__ == "__main__":
    unittest.main()
