"""Non-invasive TECH-SCOUT gateway policy and registration smoke tests."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

class FakeConnectorRegistry:
    def __init__(self):
        self.calls=[]
    def register(self,item):
        self.calls.append(item)

class TestTechScoutGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Work with package imported through repo's regular Python PYTHONPATH when tests run.
        cls.c=load("techscout_connector","cerebro-os/engines/TECH-SCOUT/connector.py")

    def test_disabled_by_default(self):
        registry=FakeConnectorRegistry()
        self.assertEqual(self.c.register_techscout(registry,self.c.TechScoutGate())["status"],"BLOCKED")
        self.assertEqual(registry.calls,[])

    def test_no_company_leak(self):
        registry=FakeConnectorRegistry()
        args=dict(enabled=True,caller_authenticated=True,policy_approved=True,audit_ready=True,rollback_ready=True)
        self.assertEqual(self.c.register_techscout(registry,self.c.TechScoutGate(environment="PROD",**args))["status"],"BLOCKED")
        self.assertEqual(registry.calls,[])

    def test_missing_gate_blocks(self):
        for field in ("caller_authenticated","policy_approved","audit_ready","rollback_ready"):
            args=dict(enabled=True,caller_authenticated=True,policy_approved=True,audit_ready=True,rollback_ready=True)
            args[field]=False
            r=FakeConnectorRegistry()
            self.assertEqual(self.c.register_techscout(r,self.c.TechScoutGate(**args))["status"],"BLOCKED")
            self.assertEqual(r.calls,[])

    def test_enabled_routes_scoped(self):
        args=dict(enabled=True,caller_authenticated=True,policy_approved=True,audit_ready=True,rollback_ready=True)
        r=FakeConnectorRegistry()
        result=self.c.register_techscout(r,self.c.TechScoutGate(company_id="fenix-capital",**args))
        self.assertEqual(result["status"],"REGISTERED_LAB")
        self.assertEqual({x.capability for x in r.calls},{"TECHSCOUT.READ","TECHSCOUT.PROPOSE"})
        self.assertTrue(all(x.company_id=="fenix-capital" and x.environment=="LAB" for x in r.calls))

if __name__=="__main__":
    unittest.main()
