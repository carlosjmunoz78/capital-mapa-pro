import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "app_crm_live_dependency_map.py"
spec = importlib.util.spec_from_file_location("app_crm_live_dependency_map", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AppCrmLiveDependencyMapTests(unittest.TestCase):
    def test_app_gateway_live_contract(self):
        result = module.assess_app_crm_live_map()
        self.assertTrue(result["app_live_verified"])
        self.assertTrue(result["crm_live_surface_verified"])
        self.assertEqual(result["project_id"], "cluhljgonannaafpmblx")

    def test_retired_sync_edges_stay_fail_closed(self):
        result = module.assess_app_crm_live_map()
        self.assertTrue(result["retired_migration_edges_fail_closed"])
        self.assertFalse(result["old_sync_endpoints_may_be_reactivated"])
        self.assertFalse(result["old_sync_endpoints_may_be_deleted"])

    def test_no_false_prod_promotion(self):
        result = module.assess_app_crm_live_map()
        self.assertEqual(result["status"], "LIVE_APP_CRM_MAP_VERIFIED_SECURITY_REVIEW_PENDING")
        self.assertFalse(result["prod_mutation_performed"])
        self.assertFalse(result["prod_candidate_allowed"])

    def test_expected_crm_surfaces_are_present(self):
        expected = {"expedientes", "tareas", "documentos", "bancos", "envios_banco", "ofertas", "tasaciones", "firmas", "inmobiliarias", "contactos", "personal_directorio", "notarias", "registros_propiedad"}
        self.assertEqual(set(module.LIVE_CRM_SURFACES), expected)


if __name__ == "__main__":
    unittest.main()
