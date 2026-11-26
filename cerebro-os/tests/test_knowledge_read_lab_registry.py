"""Offline contract checks of the additive LAB knowledge Gateway registration."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_contract_module(name, relative_path):
    spec = spec_from_file_location(name, ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise ImportError(relative_path)
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


gateway_module = load_contract_module("_knowledge_lab_gateway_service", "gateway/service.py")
connector_module = load_contract_module("_knowledge_lab_connector_registry", "connectors/registry.py")
knowledge_module = load_contract_module("_knowledge_lab_registry", "gateway/knowledge_read_lab_registry.py")
Gateway, GatewayRequest = gateway_module.Gateway, gateway_module.GatewayRequest
ConnectorRegistry, ConnectorCapability = connector_module.ConnectorRegistry, connector_module.ConnectorCapability
CAPABILITY, CONNECTOR_ID = knowledge_module.CAPABILITY, knowledge_module.CONNECTOR_ID
LAB_ENGINE_SCOPES = knowledge_module.LAB_ENGINE_SCOPES
register_knowledge_lab_capabilities = knowledge_module.register_knowledge_lab_capabilities
knowledge_lab_policy = knowledge_module.knowledge_lab_policy


class KnowledgeLabConnectorContracts(unittest.TestCase):
    def setUp(self):
        self.engines = set().union(*LAB_ENGINE_SCOPES.values())
        self.registry = ConnectorRegistry()

    def gateway(self):
        return Gateway(self.engines, self.registry, knowledge_lab_policy(lambda _req: (True, None)))

    def test_disabled_by_default(self):
        self.assertEqual(register_knowledge_lab_capabilities(
            registry=self.registry, connector_type=ConnectorCapability), ())
        answer = self.gateway().route(GatewayRequest(
            "fenix-capital", "SOC-FB-FINANCIAL-REAL-ESTATE-V1", CAPABILITY))
        self.assertEqual(answer["status"], "HUMAN_REQUIRED")

    def test_exact_scopes_and_no_cross_company(self):
        register_knowledge_lab_capabilities(registry=self.registry,
                                            connector_type=ConnectorCapability, enabled=True)
        gateway = self.gateway()
        for company, engine_ids in LAB_ENGINE_SCOPES.items():
            for engine_id in engine_ids:
                req = GatewayRequest(company, engine_id, CAPABILITY, environment="LAB")
                result = gateway.route(req)
                self.assertEqual(result["status"], "ROUTED")
                self.assertEqual(result["connector_id"], CONNECTOR_ID)
                self.assertEqual(result["environment"], "LAB")
                other = "fenix" if company == "fenix-capital" else "fenix-capital"
                denied = gateway.route(GatewayRequest(other, engine_id, CAPABILITY))
                self.assertNotEqual(denied["status"], "ROUTED")
        self.assertNotEqual(gateway.route(GatewayRequest(
            "third-company", "SOC-001/SOCBOOT-001", CAPABILITY))["status"], "ROUTED")

    def test_deny_prod_and_unrelated_capability(self):
        register_knowledge_lab_capabilities(registry=self.registry,
                                            connector_type=ConnectorCapability, enabled=True)
        g = self.gateway()
        req = GatewayRequest("fenix-capital", "SOC-FB-FINANCIAL-REAL-ESTATE-V1", CAPABILITY, "PROD")
        self.assertEqual(g.route(req)["status"], "HUMAN_REQUIRED")
        other = GatewayRequest("fenix-capital", "SOC-FB-FINANCIAL-REAL-ESTATE-V1", "PUBLISH")
        self.assertNotEqual(g.route(other)["status"], "ROUTED")

    def test_preserve_deny_policy(self):
        register_knowledge_lab_capabilities(registry=self.registry,
                                            connector_type=ConnectorCapability, enabled=True)
        deny = knowledge_lab_policy(lambda _req: (False, "SECURITY_INCIDENT"))
        gw = Gateway(self.engines, self.registry, deny)
        req = GatewayRequest("fenix-capital", "SOC-FB-FINANCIAL-REAL-ESTATE-V1", CAPABILITY)
        self.assertEqual(gw.route(req), {"status": "HUMAN_REQUIRED", "reason": "SECURITY_INCIDENT"})


if __name__ == "__main__":
    unittest.main()