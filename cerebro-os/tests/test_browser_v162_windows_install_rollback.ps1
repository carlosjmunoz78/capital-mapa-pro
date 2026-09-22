# Isolated Windows runner end-to-end installer snapshot + manual rollback test.
$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$temp=Join-Path $env:RUNNER_TEMP ('cerebro-v162-test-'+[guid]::NewGuid().ToString('N'))
$installed=Join-Path $temp 'installed'
$pkg=Join-Path $temp 'pkg'
$oldLocal=$env:LOCALAPPDATA
$server=$null
try {
 New-Item -ItemType Directory -Force -Path (Join-Path $installed 'chrome_extension_v1_4_1'),$pkg | Out-Null
 $env:LOCALAPPDATA=Join-Path $temp 'LocalAppData'
 New-Item -ItemType Directory -Force -Path $env:LOCALAPPDATA | Out-Null
 $new=(Join-Path $repo 'cerebro-os\identity\chrome_extension_v1_6_2')
 $old=(Join-Path $repo 'cerebro-os\identity\chrome_extension_v1_6_1')
 $service=(Join-Path $repo 'cerebro-os\identity\windows\CerebroBrowserBridgeService.ps1')
 Copy-Item $service (Join-Path $installed 'CerebroBrowserBridgeService.ps1')
 Copy-Item (Join-Path $old 'manifest.json') (Join-Path $installed 'chrome_extension_v1_4_1\manifest.json')
 Copy-Item (Join-Path $old 'service_worker.js') (Join-Path $installed 'chrome_extension_v1_4_1\service_worker.js')
 '{"service_version":"1.4.1","prod_enabled":false}' | Set-Content (Join-Path $installed 'package_manifest_v1_4_1.json') -Encoding UTF8
 'Write-Output "MOCK_LAUNCH"' | Set-Content (Join-Path $installed 'Start-CerebroBrowserBridge.ps1') -Encoding UTF8
 $names=@('CerebroBrowserBridgeService.ps1','chrome_extension_v1_4_1\manifest.json','chrome_extension_v1_4_1\service_worker.js')
 $prior=@{}
 foreach($name in $names){$prior[$name]=(Get-FileHash -Algorithm SHA256 (Join-Path $installed $name)).Hash}
 & python (Join-Path $repo 'cerebro-os\jobs\build_browser_replay_guard_v162.py') | Out-Null
 if($LASTEXITCODE -ne 0){throw 'PACKAGE_BUILD_FAILED'}
 $archive=(Join-Path $repo '.cerebro-runtime\packages\CEREBRO_BROWSER_REPLAY_GUARD_V1_6_2.zip')
 Expand-Archive -LiteralPath $archive -DestinationPath $pkg -Force
 $fixture=(Join-Path $repo 'cerebro-os\tests\fake_browser_bridge_health_v162.py')
 $server=Start-Process -FilePath (Get-Command python).Source -ArgumentList ('-u "'+$fixture+'"') -PassThru -WindowStyle Hidden
 $ready=$false
 for($n=0;$n -lt 40;$n++){
  try{$h=Invoke-RestMethod -UseBasicParsing -Uri 'http://127.0.0.1:8765/health' -TimeoutSec 1;if($h.status -eq 'GREEN'){$ready=$true;break}}catch{}
  Start-Sleep -Milliseconds 250
 }
 if(-not $ready){throw 'MOCK_HEALTH_NOT_READY'}
 $installer=(Join-Path $pkg 'Install-CerebroBrowserReplayGuardV162.ps1')
 & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -TargetDirectory $installed | Out-Null
 if($LASTEXITCODE -ne 0){throw 'INSTALLER_EXIT_NOT_ZERO'}
 $record=(Get-Content -Raw -LiteralPath (Join-Path $env:LOCALAPPDATA 'CEREBRO\browser-bridge\recovery-v1.6.2.json')|ConvertFrom-Json)
 if($record.status -ne 'PARTIAL' -or -not $record.checks.local_bridge -or -not $record.checks.hashes -or -not $record.backup){throw 'INSTALL_SNAPSHOT_ACCEPTANCE_FAILED'}
 $manifest=(Get-Content -Raw (Join-Path $installed 'chrome_extension_v1_4_1\manifest.json')|ConvertFrom-Json)
 if($manifest.version -ne '1.6.2'){throw 'UPGRADED_VERSION_MISMATCH'}
 & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -Rollback | Out-Null
 if($LASTEXITCODE -ne 0){throw 'ROLLBACK_EXIT_NOT_ZERO'}
 $record=(Get-Content -Raw -LiteralPath (Join-Path $env:LOCALAPPDATA 'CEREBRO\browser-bridge\recovery-v1.6.2.json')|ConvertFrom-Json)
 if($record.status -ne 'ROLLED_BACK'){throw 'ROLLBACK_REPORT_MISMATCH'}
 foreach($name in $names){if((Get-FileHash -Algorithm SHA256 (Join-Path $installed $name)).Hash -ne $prior[$name]){throw ('ROLLBACK_HASH_MISMATCH: '+$name)}}
 Write-Output 'PASS: Windows PS5.1 installer health, snapshot and byte-perfect rollback.'
}finally{
 if($server -and -not $server.HasExited){Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue}
 $env:LOCALAPPDATA=$oldLocal
}
