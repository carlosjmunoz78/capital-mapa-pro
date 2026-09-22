param([switch]$Rollback, [string]$TargetDirectory = "")

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Payload = Join-Path $Root "payload"
$Base = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { $HOME }
$Runtime = Join-Path $Base "CEREBRO\browser-bridge"
New-Item -ItemType Directory -Path $Runtime -Force | Out-Null
$StatePath = Join-Path $Runtime "recovery-v1.6.0.json"
$Files = @(
  "CerebroBrowserBridgeService.ps1",
  "CerebroBrowserTransport.ps1",
  "chrome_extension_v1_4_1\manifest.json",
  "chrome_extension_v1_4_1\service_worker.js"
)
$Result = [ordered]@{
  record_type="cerebro_browser_operator_recovery"; package_version="1.6.0"
  status="ERROR"; stage="START"; target=""; backup=""; checks=[ordered]@{}
  launcher=$null; acceptance=$null; next_gate=""; error=""; prod_enabled=$false
}

function Write-Evidence {
  $Result | ConvertTo-Json -Depth 9 | Set-Content -LiteralPath $StatePath -Encoding UTF8
  $Result | ConvertTo-Json -Depth 9
}
function Sha([string]$Path) {
  $sha = [System.Security.Cryptography.SHA256]::Create()
  $stream = [System.IO.File]::OpenRead($Path)
  try { return (($sha.ComputeHash($stream) | ForEach-Object {$_.ToString("x2")}) -join "") }
  finally { $stream.Dispose(); $sha.Dispose() }
}
function Stop-BridgeProcesses {
  $all = @(Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'")
  $stopped = @()
  foreach ($proc in $all) {
    $args = [string]$proc.CommandLine
    if ($args -and (
      ($args.Contains("CerebroBrowserTransport.ps1") -and -not $args.Contains("Start-CerebroBrowserTransport.ps1")) -or
      ($args.Contains("CerebroBrowserBridgeService.ps1") -and -not $args.Contains("Start-CerebroBrowserBridge.ps1"))
    )) {
      Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
      $stopped += $proc.ProcessId
    }
  }
  return @($stopped)
}
function Restore([string]$Target,[string]$Backup) {
  foreach ($name in $Files) {
    $old = Join-Path $Backup $name
    $new = Join-Path $Target $name
    if (Test-Path -LiteralPath $old) { Copy-Item -LiteralPath $old -Destination $new -Force }
    elseif (Test-Path -LiteralPath $new) { Remove-Item -LiteralPath $new -Force }
  }
}

try {
  if ($Rollback) {
    if (-not (Test-Path -LiteralPath $StatePath)) { throw "ROLLBACK_STATE_MISSING" }
    $old = Get-Content -Raw -LiteralPath $StatePath | ConvertFrom-Json
    if (-not $old.target -or -not $old.backup -or -not (Test-Path -LiteralPath $old.backup)) { throw "ROLLBACK_BACKUP_MISSING" }
    [void](Stop-BridgeProcesses)
    Restore ([string]$old.target) ([string]$old.backup)
    $Result.target = $old.target
    $Result.backup = $old.backup
    $Result.stage = "RESTORED"
    $Result.status = "ROLLED_BACK"
    $Result.next_gate = "START_PREVIOUS_BRIDGE"
    Write-Evidence
    exit 0
  }

  $Result.stage = "INVENTORY"
  $Target = $null
  if ($TargetDirectory) {
    $Target = (Resolve-Path -LiteralPath $TargetDirectory).Path
  } else {
    $roots = @((Split-Path -Parent $Root), (Join-Path $env:USERPROFILE "Downloads"), (Join-Path $env:USERPROFILE "Desktop"), (Join-Path $env:USERPROFILE "Documents"))
    $candidates = @()
    foreach ($searchRoot in ($roots | Select-Object -Unique)) {
      if (Test-Path -LiteralPath $searchRoot) {
        $candidates += @(Get-ChildItem -LiteralPath $searchRoot -Recurse -File -Filter "CerebroBrowserBridgeService.ps1" -ErrorAction SilentlyContinue |
          Where-Object { $_.FullName -notlike "*\work\repo\*" -and $_.FullName -notlike "*\recovery_v1_6\payload\*" -and (Test-Path (Join-Path $_.DirectoryName "CerebroBrowserTransport.ps1")) -and (Test-Path (Join-Path $_.DirectoryName "package_manifest_v1_4_1.json")) -and (Test-Path (Join-Path $_.DirectoryName "Start-CerebroBrowserBridge.ps1")) })
        if ($candidates.Count -gt 0) { break }
      }
    }
    $found = @($candidates | Sort-Object LastWriteTime -Descending | Select-Object -First 1)
    if ($found.Count -gt 0) { $Target = $found[0].DirectoryName }
  }
  if (-not $Target) { throw "EXISTING_BRIDGE_PACKAGE_NOT_FOUND" }
  $Result.target = $Target
  $manifestPath = Join-Path $Target "package_manifest_v1_4_1.json"
  if (-not (Test-Path -LiteralPath $manifestPath)) { throw "PACKAGE_MANIFEST_MISSING" }
  $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
  if ($manifest.service_version -ne "1.4.1" -or [bool]$manifest.prod_enabled) { throw "PACKAGE_SCOPE_DENIED" }
  $Result.checks.service_version = $true
  $Result.checks.prod_disabled = $true

  $extensionDir = Join-Path $Target "chrome_extension_v1_4_1"
  if (-not (Test-Path -LiteralPath (Join-Path $extensionDir "manifest.json")) -or
      -not (Test-Path -LiteralPath (Join-Path $extensionDir "service_worker.js"))) {
    $Result.status = "PARTIAL"
    $Result.next_gate = "LOCATE_EXISTING_UNPACKED_CHROME_EXTENSION"
    throw "EXISTING_EXTENSION_PATH_NOT_FOUND"
  }
  $Result.checks.existing_extension_found = $true
  if (-not (Test-Path -LiteralPath (Join-Path $Target "Start-CerebroBrowserBridge.ps1")) -or
      -not (Test-Path -LiteralPath (Join-Path $Target "Start-CerebroBrowserTransport.ps1")) -or
      -not (Test-Path -LiteralPath (Join-Path $Target "Verify-CerebroBrowserBridge.ps1"))) {
    throw "EXISTING_BRIDGE_LAUNCHERS_MISSING"
  }
  $expected = Get-Content -Raw -LiteralPath (Join-Path $Root "payload-sha256.json") | ConvertFrom-Json
  foreach ($name in $Files) {
    $new = Join-Path $Payload $name
    if (-not (Test-Path -LiteralPath $new)) { throw "PAYLOAD_MISSING" }
    if ((Sha $new) -ne [string]$expected.$($name.Replace("\","/"))) { throw "PAYLOAD_HASH_MISMATCH" }
  }
  $Result.checks.payload_hashes = $true
  $manifestExt = Get-Content -Raw -LiteralPath (Join-Path $Payload "chrome_extension_v1_4_1\\manifest.json") | ConvertFrom-Json
  if ([string]$manifestExt.version -ne "1.6.0" -or @($manifestExt.host_permissions).Count -ne 2 -or
      "http://127.0.0.1/*" -notin @($manifestExt.host_permissions) -or "https://example.com/*" -notin @($manifestExt.host_permissions)) {
    throw "EXTENSION_HOST_SCOPE_INVALID"
  }
  $Result.checks.extension_host_scope = $true

  $Result.stage = "SNAPSHOT"
  $Backup = Join-Path $Runtime ("recovery-backup-v160-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
  New-Item -ItemType Directory -Path $Backup -Force | Out-Null
  $Result.backup = $Backup
  foreach ($name in $Files) {
    $original = Join-Path $Target $name
    $copy = Join-Path $Backup $name
    New-Item -ItemType Directory -Path (Split-Path -Parent $copy) -Force | Out-Null
    Copy-Item -LiteralPath $original -Destination $copy -Force
  }
  Write-Evidence | Out-Null

  $Result.stage = "INSTALL"
  $Result.checks.stopped_bridge_processes = @(Stop-BridgeProcesses).Count
  foreach ($name in $Files) {
    Copy-Item -LiteralPath (Join-Path $Payload $name) -Destination (Join-Path $Target $name) -Force
  }

  $Result.stage = "START"
  $launch = & (Join-Path $Target "Start-CerebroBrowserBridge.ps1")
  $Result.launcher = "STARTER_INVOKED"
  Start-Sleep -Seconds 3
  $Result.stage = "VERIFY"
  $verification = & (Join-Path $Target "Verify-CerebroBrowserBridge.ps1")
  $Result.acceptance = ($verification | ConvertFrom-Json)
  $Result.status = if ($Result.acceptance.status -eq "GREEN") { "PARTIAL" } else { "PARTIAL" }
  $Result.next_gate = "RELOAD_EXISTING_CHROME_EXTENSION_V160_AND_REMOTE_OPERATOR_LAB_ROUNDTRIP"
  Write-Evidence
  exit 0
} catch {
  $Result.error = $_.Exception.Message
  if ($Result.backup -and $Result.target -and $Result.stage -in @("INSTALL","START","VERIFY")) {
    [void](Stop-BridgeProcesses)
    Restore $Result.target $Result.backup
    $Result.status = "ROLLED_BACK"
    $Result.next_gate = "START_PREVIOUS_BRIDGE"
  }
  Write-Evidence
  exit 1
}
