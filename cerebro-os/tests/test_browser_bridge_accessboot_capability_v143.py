import pathlib
import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location

ROOT = pathlib.Path(__file__).resolve().parents[1]
WIN = ROOT / "identity" / "windows"
TRANSPORT = (WIN / "CerebroBrowserTransport.ps1").read_text(encoding="utf-8")
INSTALLER = (WIN / "recovery_v1_4_3" / "Install-CerebroBrowserTransportRecovery.ps1").read_text(encoding="utf-8")


class AccessbootCapabilitySnapshotV143Tests(unittest.TestCase):
    def test_snapshot_action_is_zero_mutation_and_secret_free_by_contract(self):
        self.assertIn('ACCESSBOOT_CAPABILITY_SNAPSHOT', TRANSPORT)
        self.assertIn('evidence_ref = "ACCESSBOOT_CAPABILITY_SNAPSHOT"', TRANSPORT)
        self.assertIn('external_mutation_performed = $false', TRANSPORT)
        self.assertIn('secret_value_included = $false', TRANSPORT)
        self.assertIn('extension_connected', TRANSPORT)
        self.assertIn('transport_online', TRANSPORT)
        self.assertIn('chrome_profiles', TRANSPORT)
        self.assertIn('REMOTE_ACTION_DENIED', TRANSPORT)
        snapshot = TRANSPORT.split('if ($action -eq "ACCESSBOOT_CAPABILITY_SNAPSHOT")', 1)[1].split('if ($action -ne "OPEN_LOCAL_TEST_PAGE")', 1)[0]
        for forbidden in ('password', 'token', 'cookie', 'credential_value', 'chrome_user_data_dir', 'extension_id'):
            self.assertNotIn(forbidden, snapshot.lower())

    def test_v143_installer_updates_only_transport_and_has_rollback(self):
        self.assertIn("$files = @('CerebroBrowserTransport.ps1')", INSTALLER)
        self.assertIn('Restore-Files', INSTALLER)
        self.assertIn('Stop-TransportWorkers', INSTALLER)
        self.assertIn('Verify-CerebroBrowserBridge.ps1', INSTALLER)
        self.assertNotIn('Stop-Process -Name chrome', INSTALLER)
        self.assertNotIn('CerebroBrowserBridgeService.ps1 -Destination', INSTALLER)

    def test_v143_recovery_zip_has_no_pairing_or_prod_payload(self):
        spec = spec_from_file_location(
            'accessboot_recovery_builder',
            ROOT / 'jobs' / 'build_browser_bridge_accessboot_recovery_v143.py',
        )
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            archive = pathlib.Path(temp) / 'accessboot-recovery.zip'
            result = module.build(archive)
            self.assertFalse(result['prod_enabled'])
            self.assertFalse(result['pairing_included'])
            self.assertFalse(result['external_mutation_allowed'])
            self.assertEqual(result['capability'], 'ACCESSBOOT_CAPABILITY_SNAPSHOT')
            import zipfile
            with zipfile.ZipFile(archive) as package:
                names = set(package.namelist())
                self.assertEqual(
                    names,
                    {
                        'INSTALL_AND_VERIFY.bat',
                        'Install-CerebroBrowserTransportRecovery.ps1',
                        'ROLLBACK.bat',
                        'README.txt',
                        'payload/CerebroBrowserTransport.ps1',
                        'payload-sha256.json',
                    },
                )


if __name__ == '__main__':
    unittest.main()
