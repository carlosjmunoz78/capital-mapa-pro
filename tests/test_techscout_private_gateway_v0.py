"""TECH-SCOUT register+existing CEREBRO Gateway integration regression tests."""
import importlib.util
from pathlib import Path
import unittest
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))
def load(name,relative):
    spec=importlib.util.spec_from_file_location(name,ROOT/relative)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod
    spec.loader.exec_module(mod)
    return mod

class TestTechScoutIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=load("techscout_connector","cerebro-os/engines/TECH-SCOUT/connector.py")
        cls.core=load("techscout_gateway","cerebro-os/gateway/service.py")
        cls.registry=load("techscout_registry","cerebro-os/connectors/registry.py")

    def allowed(self,**kwargs):
        d=dict(company_id="fenix-capital",engine_id="TECH-SCOUT",version="0.1.0",environment="LAB",enabled=True,caller_authenticated=True,policy_approved=True,audit_ready=True,rollback_ready=True,money_limit_eur=0)
        d.update(kwargs);return self.c.TechScoutGate(**d)

    def route(self,gate,company="fenix-capital",cap="TECHSCOUT.READ",policy=None,env="LAB"):
        registry=self.registry.ConnectorRegistry()
        status=self.c.register_techscout(registry,gate)
        gateway=self.core.Gateway({"TECH-SCOUT"},registry,policy_check=policy)
        return status,gateway.route(self.core.GatewayRequest(company_id=company,engine_id="TECH-SCOUT",capability=cap,environment=env,version="0.1.0"))

    def test_off_by_default(self):
        status,route=self.route(self.c.TechScoutGate())
        self.assertEqual(status["status"],"BLOCKED")
        self.assertEqual(route["status"],"HUMAN_REQUIRED")

    def test_missing_gate_fail_closed(self):
        for field in ("caller_authenticated","policy_approved","audit_ready","rollback_ready","enabled"):
            status,route=self.route(self.allowed(**{field:False}))
            self.assertEqual(status["status"],"BLOCKED",field)
            self.assertNotEqual(route["status"],"ROUTED")

    def test_wrong_company_in_grant_denied(self):
        status,route=self.route(self.allowed(company_id=""))
        self.assertEqual(status["status"],"BLOCKED")
        self.assertEqual(route["status"],"HUMAN_REQUIRED")

    def test_prod_or_preprod_never_eligible(self):
        for env in ("PROD","PREPROD"):
            status,route=self.route(self.allowed(environment=env),env=env)
            self.assertEqual(status["status"],"BLOCKED")
            self.assertNotEqual(route["status"],"ROUTED")

    def test_money_limit_fail_closed(self):
        status,route=self.route(self.allowed(money_limit_eur=1))
        self.assertEqual(status["status"],"BLOCKED")

    def test_policy_denial_blocks_existing_gateway(self):
        status,route=self.route(self.allowed(),policy=lambda r:(False,"POLICY_CONFLICT"))
        self.assertEqual(status["status"],"REGISTERED_LAB")
        self.assertEqual(route["status"],"HUMAN_REQUIRED")

    def test_all_three_lab_capabilities_route_if_gates_true(self):
        for cap in self.c.CAPABILITIES:
            status,route=self.route(self.allowed(),cap=cap)
            self.assertEqual(status["status"],"REGISTERED_LAB")
            self.assertEqual(route["status"],"ROUTED")
            self.assertEqual(route["engine_id"],"TECH-SCOUT")

    def test_cross_company_denied(self):
        status,route=self.route(self.allowed(),company="other")
        self.assertEqual(status["status"],"REGISTERED_LAB")
        self.assertNotEqual(route["status"],"ROUTED")

    def test_unknown_capability_denied(self):
        status,route=self.route(self.allowed(),cap="TECHSCOUT.ADMIN")
        self.assertNotEqual(route["status"],"ROUTED")

    def test_invalid_version_denied(self):
        status,route=self.route(self.allowed(version="9.9.9"))
        self.assertEqual(status["status"],"BLOCKED")
