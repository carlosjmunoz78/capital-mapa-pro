param([string]$TargetDirectory = "")
$ErrorActionPreference = "Stop"
$Runtime = Join-Path $env:LOCALAPPDATA "CEREBRO\browser-bridge"
$Report = Join-Path $Runtime "autostart-v162-result.json"
New-Item -ItemType Directory -Force -Path $Runtime | Out-Null
$Outcome = [ordered]@{ at=(Get-Date -Format o); status="ERROR";stage="START";port=0;service="";reason="" }
function Save-Outcome { ($Outcome | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath $Report -Encoding UTF8 }
function Get-Bridge([int]$Port) {
  try {
    $h=Invoke-RestMethod -UseBasicParsing -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 1
    if ($h.service -eq "CEREBRO Browser Bridge" -and $h.service_version -eq "1.4.1" -and
        $h.company_id -eq "fenix" -and $h.environment -eq "LAB" -and $h.version -eq "v0" -and
        [bool]$h.paired -and [bool]$h.kill_switch_enabled -and $h.status -eq "GREEN") { return $h }
  } catch {}
  return $null
}
function Is-PortFree([int]$Port) {
  $listener=$null
  try {
    $listener=[System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback,$Port)
    $listener.Start()
    return $true
  } catch {return $false}
  finally {if ($listener) {$listener.Stop()}}
}
try {
  # Idempotent: do not launch a second Bridge or disturb unrelated 8765 service.
  $Outcome.stage="DISCOVER"
  foreach($port in 8765..8785) {
    $h=Get-Bridge $port
    if($h) {
      $Outcome.status="EXISTING"; $Outcome.port=$port; $Outcome.service="CEREBRO Browser Bridge"
      Save-Outcome
      exit 0
    }
  }
  $Outcome.stage="PORT_RESERVE"
  if(-not (Is-PortFree 8766)) {throw "PREFERRED_PORT_8766_OCCUPIED_FAIL_CLOSED"}
  $record=Join-Path $Runtime "recovery-v1.6.2.json"
  if(-not $TargetDirectory) {
    if(-not (Test-Path -LiteralPath $record)) {throw "V162_RECOVERY_RECORD_MISSING"}
    $state=Get-Content -Raw -LiteralPath $record | ConvertFrom-Json
    if($state.package_version -ne "1.6.2" -or $state.status -notin @("PARTIAL","ACCEPTED") -or
       [bool]$state.prod_enabled) {throw "RECOVERY_SCOPE_DENIED"}
    $TargetDirectory=[string]$state.target
  }
  if(-not (Test-Path -LiteralPath $TargetDirectory -PathType Container)) {throw "BRIDGE_TARGET_MISSING"}
  $launcher=Join-Path $TargetDirectory "Start-CerebroBrowserBridge.ps1"
  if(-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {throw "BRIDGE_LAUNCHER_MISSING"}
  $manifest=Join-Path $TargetDirectory "package_manifest_v1_4_1.json"
  if(-not (Test-Path -LiteralPath $manifest)) {throw "BRIDGE_MANIFEST_MISSING"}
  $m=Get-Content -Raw -LiteralPath $manifest | ConvertFrom-Json
  if($m.service_version -ne "1.4.1" -or [bool]$m.prod_enabled) {throw "BRIDGE_MANIFEST_SCOPE_DENIED"}
  $Outcome.stage="LAUNCH"
  $previousPort=$env:CEREBRO_BRIDGE_PORT
  try {
    $env:CEREBRO_BRIDGE_PORT="8766"
    & $launcher | Out-Null
  } finally {
    if($null -eq $previousPort) {Remove-Item Env:CEREBRO_BRIDGE_PORT -ErrorAction SilentlyContinue}
    else {$env:CEREBRO_BRIDGE_PORT=$previousPort}
  }
  $Outcome.stage="VERIFY"
  $h=$null
  for($attempt=1;$attempt -le 20;$attempt++) {
    $h=Get-Bridge 8766
    if($h) {break}
    Start-Sleep -Seconds 1
  }
  if(-not $h) {throw "BRIDGE_8766_NOT_READY"}
  $Outcome.status="GREEN";$Outcome.port=8766;$Outcome.service="CEREBRO Browser Bridge"
} catch {
  $Outcome.reason=$_.Exception.Message
  $Outcome.status="ERROR"
} finally {Save-Outcome}
if($Outcome.status -ne "GREEN") {exit 1}
