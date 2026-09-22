import http.server
import json
import pathlib
import shutil
import subprocess
import tempfile
import threading
import unittest
import os
from importlib.util import module_from_spec, spec_from_file_location

ROOT = pathlib.Path(__file__).resolve().parents[1]
WIN = ROOT / 'identity' / 'windows'
TRANSPORT = (WIN / 'CerebroBrowserTransport.ps1').read_text(encoding='utf-8')
LAUNCHER = (WIN / 'Start-CerebroBrowserTransport.ps1').read_text(encoding='utf-8')
INSTALLER = (WIN / 'recovery_v1_4_2' / 'Install-CerebroBrowserTransportRecovery.ps1').read_text(encoding='utf-8')


class RecoveryContractTests(unittest.TestCase):
    def test_scope_and_remote_action_remain_closed(self):
        for marker in ('BRIDGE_SCOPE_DENIED', 'CREDENTIAL_SCOPE_MISMATCH', 'REMOTE_SCOPE_MISMATCH',
                       'REMOTE_ACTION_DENIED', 'OPEN_LOCAL_TEST_PAGE', 'external_mutation_performed = $false'):
            self.assertIn(marker, TRANSPORT)
        self.assertNotIn('PROD', LAUNCHER)

    def test_launcher_and_worker_do_not_put_secrets_on_command_line(self):
        self.assertIn('transport-local-key-1.4.1.txt', LAUNCHER)
        self.assertNotIn('-TransportKey', LAUNCHER)
        self.assertNotIn('-PairCode', LAUNCHER)
        self.assertIn('$curlArguments = "--config -"', TRANSPORT)
        self.assertIn('$psi.RedirectStandardInput = $true', TRANSPORT)
        self.assertIn('$psi.Arguments = $curlArguments', TRANSPORT)
        self.assertIn('$proc.StandardInput.BaseStream.Write($configBytes, 0, $configBytes.Length)', TRANSPORT)
        self.assertIn('New-Object System.Text.UTF8Encoding($false)', TRANSPORT)
        self.assertNotIn('StandardInputEncoding', TRANSPORT)
        self.assertIn('$curlArguments += " --data-binary `"@$bodyPath`""', TRANSPORT)
        self.assertNotIn('-H "Authorization:', TRANSPORT)

    def test_launcher_observes_pid_exit_and_both_streams(self):
        for marker in ('8765..8785', '$worker.Id', '$worker.HasExited', 'RedirectStandardOutput',
                       'RedirectStandardError', "'BRIDGE_NOT_FOUND'", "'SCOPE_DENIED'"):
            self.assertIn(marker, LAUNCHER)

    def test_worker_logs_stages_and_preserves_one_time_pairing(self):
        for marker in ('BOOT_START', 'ARGS_VALIDATED', 'MUTEX_ACQUIRED', 'CURL_PROCESS_EXIT',
                       'CREDENTIAL_SAVED', 'PAIRING_FILE_REMOVED', 'WORKER_EXIT',
                       'ConvertFrom-SecureString', 'ConvertTo-SecureString'):
            self.assertIn(marker, TRANSPORT)
        self.assertLess(TRANSPORT.index('if ($response.decision -ne "ENROLLED")'), TRANSPORT.index('Save-Credential $token $Bridge'))
        self.assertLess(TRANSPORT.index('Save-Credential $token $Bridge'), TRANSPORT.index('Remove-Item -LiteralPath $PairingFile'))

    def test_installer_is_scoped_and_has_rollback(self):
        for marker in ('function Get-Sha256', 'Restore-Files', 'Stop-TransportWorkers',
                       'Start-CerebroBrowserTransport.ps1', 'Verify-CerebroBrowserBridge.ps1'):
            self.assertIn(marker, INSTALLER)
        self.assertNotIn('Stop-Process -Name chrome', INSTALLER)
        self.assertNotIn('CerebroBrowserBridgeService.ps1 -Destination', INSTALLER)

    def test_recovery_zip_contains_only_expected_files(self):
        spec = spec_from_file_location('recovery_builder', ROOT / 'jobs' / 'build_browser_bridge_transport_recovery_v142.py')
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            archive = pathlib.Path(temp) / 'recovery.zip'
            result = module.build(archive)
            self.assertFalse(result['prod_enabled'])
            self.assertFalse(result['pairing_included'])
            import zipfile
            with zipfile.ZipFile(archive) as package:
                names = package.namelist()
                self.assertIn('INSTALL_AND_VERIFY.bat', names)
                self.assertIn('ROLLBACK.bat', names)
                self.assertNotIn('PAIRING_ONCE.txt', names)
                self.assertFalse(any('chrome_extension' in name for name in names))


class CurlWindowsContractTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('powershell.exe'), 'Windows PowerShell 5.1 required')
    def test_failed_install_restores_previous_transport(self):
        spec = spec_from_file_location('recovery_builder', ROOT / 'jobs' / 'build_browser_bridge_transport_recovery_v142.py')
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(prefix='Cerebro Recovery Test ') as temp:
            base = pathlib.Path(temp)
            archive = base / 'recovery.zip'
            module.build(archive)
            import zipfile
            extracted = base / 'extracted'
            with zipfile.ZipFile(archive) as package:
                package.extractall(extracted)
            target = base / 'old package'
            target.mkdir()
            (target / 'CerebroBrowserBridgeService.ps1').write_text('old service', encoding='utf-8')
            (target / 'CerebroBrowserTransport.ps1').write_text('old transport', encoding='utf-8')
            (target / 'package_manifest_v1_4_1.json').write_text(json.dumps({'service_version': '1.4.1', 'prod_enabled': False}), encoding='utf-8')
            env = os.environ.copy()
            env['LOCALAPPDATA'] = str(base / 'runtime')
            run = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                                  str(extracted / 'Install-CerebroBrowserTransportRecovery.ps1'),
                                  '-TargetDirectory', str(target)], capture_output=True, text=True, timeout=60, env=env)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual((target / 'CerebroBrowserTransport.ps1').read_text(encoding='utf-8'), 'old transport')
            state = json.loads((base / 'runtime' / 'CEREBRO' / 'browser-bridge' / 'recovery-v1.4.2.json').read_text(encoding='utf-8-sig'))
            self.assertEqual(state['status'], 'ROLLED_BACK', state)

    @unittest.skipUnless(shutil.which('powershell.exe'), 'Windows PowerShell 5.1 required')
    def test_post_body_is_utf8_without_bom_and_safe_with_spaces(self):
        observed = {}

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                observed['body'] = self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"decision":"ENROLLED"}')

            def log_message(self, *_):
                pass

        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            function = TRANSPORT.split('function Invoke-CurlJson', 1)[1].split('function Gateway-Call', 1)[0]
            with tempfile.TemporaryDirectory(prefix='Cerebro Path With Spaces ') as temp:
                path = pathlib.Path(temp) / 'probe.ps1'
                path.write_text(
                    '$ErrorActionPreference="Stop"\n$RuntimeDir="' + temp + '"\n'
                    'function Log { param($a,$b,$c,$d) }\n'
                    'function Invoke-CurlJson' + function + '\n'
                    '$r=Invoke-CurlJson -Method "POST" -Uri "http://127.0.0.1:' + str(server.server_port) +
                    '/" -Body @{probe="ok"}; if($r.decision -ne "ENROLLED"){exit 2}\n', encoding='utf-8')
                run = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(path)],
                                     capture_output=True, text=True, timeout=15)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertFalse(observed['body'].startswith(b'\xef\xbb\xbf'))
                self.assertEqual(json.loads(observed['body']), {'probe': 'ok'})
        finally:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    unittest.main()
