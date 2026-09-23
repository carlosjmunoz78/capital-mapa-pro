param([switch]$Rollback)
$ErrorActionPreference='Stop'
$Runtime=Join-Path $env:LOCALAPPDATA 'CEREBRO\browser-bridge'
$Record=Join-Path $Runtime 'reboot-autostart-v0.json'
$StartupDir=[Environment]::GetFolderPath('Startup')
$StartupFile=Join-Path $StartupDir 'CEREBRO_BROWSER_BRIDGE_FENIX_LAB.cmd'
$Report=[ordered]@{record_type='cerebro_browser_bridge_reboot_autostart';version='v0';status='ERROR';stage='INIT';target='';startup_file=$StartupFile;backup='';port=8766;checks=[ordered]@{};error='';prod_enabled=$false}
function Save-Report { New-Item -ItemType Directory -Force -Path $Runtime|Out-Null; $Report|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $Record -Encoding UTF8; $Report|ConvertTo-Json -Depth 8 }
try {
  if($Rollback){
    if(-not(Test-Path $Record)){throw 'ROLLBACK_STATE_MISSING'}
    $old=Get-Content -Raw -LiteralPath $Record|ConvertFrom-Json
    if(Test-Path $StartupFile){Remove-Item -LiteralPath $StartupFile -Force}
    if($old.backup -and (Test-Path $old.backup)){Copy-Item -LiteralPath $old.backup -Destination $StartupFile -Force}
    $Report.status='ROLLED_BACK';$Report.stage='RESTORED';$Report.backup=[string]$old.backup;$Report.target=[string]$old.target
    Save-Report; exit 0
  }
  $Report.stage='INVENTORY'
  $v162=Join-Path $Runtime 'recovery-v1.6.2.json'
  if(-not(Test-Path $v162)){throw 'V162_RECOVERY_RECORD_MISSING'}
  $rec=Get-Content -Raw -LiteralPath $v162|ConvertFrom-Json
  if($rec.package_version -ne '1.6.2' -or $rec.status -notin @('PARTIAL','GREEN')){throw 'V162_NOT_ACCEPTED_ENOUGH'}
  $Target=[string]$rec.target
  if(-not(Test-Path $Target)){throw 'BRIDGE_TARGET_MISSING'}
  foreach($f in @('Start-CerebroBrowserBridge.ps1','CerebroBrowserBridgeService.ps1','Start-CerebroBrowserTransport.ps1','CerebroBrowserTransport.ps1')){if(-not(Test-Path (Join-Path $Target $f))){throw "BRIDGE_FILE_MISSING_$f"}}
  $Report.target=$Target
  $Report.checks.v162_record=$true
  $Report.checks.no_admin_required=$true
  $Report.checks.prod_disabled=$true
  $Report.stage='SNAPSHOT'
  if(Test-Path $StartupFile){
    $Backup=Join-Path $Runtime ('reboot-autostart-v0-backup-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.cmd')
    Copy-Item -LiteralPath $StartupFile -Destination $Backup -Force
    $Report.backup=$Backup
  }
  $Report.stage='INSTALL'
  $escaped=$Target.Replace('%','%%')
  $cmd=@"
@echo off
setlocal
set "CEREBRO_BRIDGE_PORT=8766"
timeout /t 5 /nobreak >nul
start "" /min powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "$escaped\Start-CerebroBrowserBridge.ps1"
exit /b 0
"@
  Set-Content -LiteralPath $StartupFile -Value $cmd -Encoding ASCII
  $Report.stage='VERIFY'
  $body=Get-Content -Raw -LiteralPath $StartupFile
  if($body -notmatch 'CEREBRO_BRIDGE_PORT=8766'){throw 'STARTUP_PORT_PIN_MISSING'}
  if($body -notmatch [regex]::Escape($Target)){throw 'STARTUP_TARGET_MISMATCH'}
  $Report.checks.startup_file=$true
  $Report.checks.pinned_port_8766=$true
  $Report.status='GREEN';$Report.stage='INSTALLED';Save-Report;exit 0
} catch {
  $Report.error=$_.Exception.Message
  Save-Report
  exit 1
}
