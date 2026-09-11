import os
import sys
import tempfile
import unittest
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


canonical = load("canonical_loader_mod", "registry/canonical_loader.py")
mass = load("mass_scaffold_mod", "factory/mass_scaffold.py")
store_mod = load("sqlite_store_mod", "runtime/sqlite_store.py")
vault = load("vault_adapter_mod", "identity/vault_adapter.py")
conn_mod = load("connector_registry_mod", "connectors/registry.py")
gateway_mod = load("gateway_service_mod", "gateway/service.py")
resilience = load("resilience_exec_mod", "resilience/executable.py")


class NextLoopTests(unittest.TestCase):
    def test_canonical_registry_is_exactly_177_unique_ids(self):
        ids = canonical.canonical_engine_ids()
        self.assertEqual(177, len(ids))
        self.assertEqual(177, len(set(ids)))
        self.assertIn("FACT-001", ids)
        self.assertIn("CONSOLE-001", ids)
        self.assertIn("LAB-TRD", ids)

    def test_mass_scaffold_generates_all_177_in_temp_lab(self):
        ids = canonical.canonical_engine_ids()
        with tempfile.TemporaryDirectory() as td:
            created = mass.generate_all(Path(td), ids)
            self.assertEqual(177, len(created))
            self.assertTrue(all((p / "manifest.json").exists() for p in created))
            self.assertTrue(all((p / "ops" / "rollback.md").exists() for p in created))

    def test_sqlite_runtime_persistence_is_idempotent_and_tenant_scoped(self):
        with tempfile.TemporaryDirectory() as td:
            db = store_mod.SQLiteRuntimeStore(Path(td) / "runtime.db")
            self.assertTrue(db.put(kind="EVENT", idempotency_key="k1", company_id="c1", engine_id="EVT-001", version="0.1.0", environment="LAB", payload={"x": 1}))
            self.assertFalse(db.put(kind="EVENT", idempotency_key="k1", company_id="c1", engine_id="EVT-001", version="0.1.0", environment="LAB", payload={"x": 2}))
            self.assertTrue(db.put(kind="EVENT", idempotency_key="k1", company_id="c2", engine_id="EVT-001", version="0.1.0", environment="LAB", payload={"x": 3}))
            self.assertTrue(db.put(kind="EVENT", idempotency_key="k1", company_id="c1", engine_id="EVT-001", version="0.1.0", environment="PROD", payload={"x": 4}))
            self.assertEqual(2, len(db.list_for_company("c1")))
            self.assertEqual(1, len(db.list_for_company("c2")))
            with self.assertRaises(ValueError):
                db.put(kind="EVENT", idempotency_key="k2", company_id="c1", engine_id="EVT-001", version="0.1.0", environment="DEV", payload={})
            with self.assertRaises(ValueError):
                db.list_for_company("")
            db.close()

    def test_vault_adapter_never_accepts_embedded_secret(self):
        with self.assertRaises(ValueError):
            vault.SecretRef("ENV", "token=abc").validate()
        os.environ["CEREBRO_TEST_SECRET"] = "secret-value"
        try:
            adapter = vault.EnvVaultAdapter()
            self.assertEqual("secret-value", adapter.resolve(vault.SecretRef("ENV", "CEREBRO_TEST_SECRET")))
            self.assertEqual("***REDACTED***", vault.redact("secret-value"))
        finally:
            os.environ.pop("CEREBRO_TEST_SECRET", None)

    def test_connector_priority_and_gateway_policy(self):
        registry = conn_mod.ConnectorRegistry()
        registry.register(conn_mod.ConnectorCapability("browser", "status.read", "BROWSER"))
        registry.register(conn_mod.ConnectorCapability("api", "status.read", "OFFICIAL_API"))
        selected = registry.route("status.read", "fenix")
        self.assertEqual("api", selected.connector_id)

        gw = gateway_mod.Gateway({"SUP-001"}, registry)
        routed = gw.route(gateway_mod.GatewayRequest("fenix", "SUP-001", "status.read"))
        self.assertEqual("ROUTED", routed["status"])
        self.assertEqual("LAB", routed["environment"])
        self.assertEqual("1.0.0", routed["version"])
        blocked = gateway_mod.Gateway({"SUP-001"}, registry, policy_check=lambda request: (False, "POLICY_CONFLICT"))
        result = blocked.route(gateway_mod.GatewayRequest("fenix", "SUP-001", "status.read"))
        self.assertEqual({"status": "HUMAN_REQUIRED", "reason": "POLICY_CONFLICT"}, result)

    def test_gateway_never_routes_lab_only_connector_into_prod(self):
        registry = conn_mod.ConnectorRegistry()
        registry.register(conn_mod.ConnectorCapability("lab-api", "status.read", "OFFICIAL_API", environment="LAB"))
        registry.register(conn_mod.ConnectorCapability("prod-browser", "status.read", "BROWSER", environment="PROD"))
        gw = gateway_mod.Gateway({"SUP-001"}, registry)
        routed = gw.route(gateway_mod.GatewayRequest("fenix", "SUP-001", "status.read", environment="PROD", version="2.0.0"))
        self.assertEqual("ROUTED", routed["status"])
        self.assertEqual("prod-browser", routed["connector_id"])
        self.assertEqual("PROD", routed["environment"])
        self.assertEqual("2.0.0", routed["version"])

    def test_executable_backup_restore_and_rebuild(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.txt"
            source.write_text("cerebro", encoding="utf-8")
            backup = root / "backup" / "source.txt"
            digest = resilience.backup_file(source, backup)
            target = root / "restored" / "source.txt"
            resilience.restore_file(backup, target, digest)
            self.assertEqual("cerebro", target.read_text(encoding="utf-8"))
            rebuild = root / "rebuild"
            resilience.rebuild_directory(rebuild, ("config", "contracts", "ops"))
            self.assertTrue((rebuild / "ops").is_dir())


if __name__ == "__main__":
    unittest.main()
