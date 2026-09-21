import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
WIN=ROOT/"identity"/"windows"

class BrowserBridgeWindowsNativePackageV1Tests(unittest.TestCase):
    def test_native_package_has_no_python_runtime_dependency(self):
        launcher=(WIN/"Start-CerebroBrowserBridge.ps1").read_text(encoding="utf-8")
        bat=(WIN/"START_CEREBRO_BROWSER_BRIDGE.bat").read_text(encoding="utf-8")
        self.assertNotIn("python",launcher.lower())
        self.assertNotIn("py -3",launcher.lower())
        self.assertNotIn("python",bat.lower())
        self.assertIn("CerebroBrowserBridgeService.ps1",launcher)

    def test_launcher_validates_service_identity_and_port_collision(self):
        launcher=(WIN/"Start-CerebroBrowserBridge.ps1").read_text(encoding="utf-8")
        self.assertIn("CEREBRO Browser Bridge",launcher)
        self.assertIn("8766..8785",launcher)
        self.assertIn("Test-PortFree",launcher)
        self.assertIn("/health",launcher)
        self.assertIn("launcher.log",launcher)

    def test_service_is_loopback_and_fail_closed_for_prod(self):
        service=(WIN/"CerebroBrowserBridgeService.ps1").read_text(encoding="utf-8")
        self.assertIn("[System.Net.IPAddress]::Loopback",service)
        self.assertIn('@("LAB","PREPROD")',service)
        self.assertIn('cloud_transport_status = "NOT_CONFIGURED"',service)
        self.assertNotIn("0.0.0.0",service)

    def test_form_collects_no_credentials(self):
        service=(WIN/"CerebroBrowserBridgeService.ps1").read_text(encoding="utf-8")
        self.assertIn('form method="get"',service)
        self.assertIn('Empresa',service)
        self.assertIn('Perfil del navegador',service)
        self.assertNotIn('type="password"',service.lower())

if __name__=="__main__":
    unittest.main()
