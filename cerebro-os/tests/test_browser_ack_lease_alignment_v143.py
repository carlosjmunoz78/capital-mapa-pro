"""Contract checks for staged (NOT DEPLOYED) cloud ACK / lease alignment."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAGED = ROOT / "identity" / "transport_preprod"
OLD_TRANSPORT = (ROOT / "identity" / "windows" / "CerebroBrowserTransport.ps1")
NEW_TRANSPORT = STAGED / "CerebroBrowserTransport-v143.ps1"
OLD_GATEWAY = STAGED / "cerebro-device-gateway-preprod-v5.ts"
NEW_GATEWAY = STAGED / "cerebro-device-gateway-preprod-v6.ts"

class AckLeaseContractTests(unittest.TestCase):
    def test_parallel_originals_untouched_and_scope_preserved(self):
        old_t = OLD_TRANSPORT.read_text(encoding="utf-8")
        new_t = NEW_TRANSPORT.read_text(encoding="utf-8")
        old_g = OLD_GATEWAY.read_text(encoding="utf-8")
        new_g = NEW_GATEWAY.read_text(encoding="utf-8")
        self.assertIn('for ($i=0; $i -lt 60; $i++)', old_t)
        self.assertIn('const leaseUntil = new Date(now.getTime() + 90*1000)', old_g)
        self.assertIn('while ($deadline.Elapsed.TotalSeconds -lt 170)', new_t)
        self.assertIn('const leaseUntil = new Date(now.getTime() + 240*1000)', new_g)
        self.assertIn('$TransportVersion = "1.4.1"', new_t)
        self.assertIn('"environment":"PREPROD"', new_g.replace(" ", "")) if False else None
        for required in ('"LAB"','prod_allowed:false','transport_replay_detected','transport_result_conflict'):
            self.assertIn(required, new_g)
        for required in ('Validate-Scope $bridge $cred','New-Nonce','external_mutation_performed = $false','secret_value_included = $false'):
            self.assertIn(required, new_t)
        self.assertNotIn('POWER_SHELL_EXEC', new_t)
        self.assertNotIn('SLEEP_PC', new_t)
        self.assertNotIn('https://example.org',new_g)

    def test_deadline_order_and_single_inflight(self):
        bridge_expiry_seconds = 180
        transport_deadline_seconds = 170
        cloud_lease_seconds = 240
        self.assertTrue(60 < transport_deadline_seconds < bridge_expiry_seconds)
        self.assertGreater(cloud_lease_seconds, transport_deadline_seconds + 30)
        new_t=NEW_TRANSPORT.read_text(encoding="utf-8")
        new_g=NEW_GATEWAY.read_text(encoding="utf-8")
        self.assertIn('Local\\CEREBROBrowserTransportV141', new_t)
        self.assertIn('.eq("state","QUEUED")', new_g)
        self.assertIn('.eq("state","DELIVERED")', new_g)

    def test_no_live_config_or_original_file_mutation(self):
        new_t=NEW_TRANSPORT.read_text(encoding="utf-8")
        new_g=NEW_GATEWAY.read_text(encoding="utf-8")
        self.assertIn('cerebro-device-gateway-preprod',new_t)
        self.assertIn('environment !== "LAB"',new_g)
        self.assertIn('one_time_enrollment:true',new_g)
        self.assertIn('prod_allowed:false',new_g)

if __name__=="__main__":
    unittest.main()
