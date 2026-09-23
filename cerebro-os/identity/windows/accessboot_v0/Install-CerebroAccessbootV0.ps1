param([switch]$Rollback,[string]$TargetDirectory="")
$ErrorActionPreference="Stop"
$Root=$PSScriptRoot
$Runtime=Join-Path $env:LOCALAPPDATA "CEREBRO\browser-bridge"
$Record=Join-Path $Runtime "accessboot-v0.json"
$Managed=@(
  "CerebroBrowserBridgeService.ps1",
  "CerebroBrowserTransport.ps1",
  "chrome_extension_v1_4_1\manifest.json",
  "chrome_extension_v1_4_1\service_worker.js"
)
$Report=[ordered]@{record_type="cerebro_accessboot_windows_operator";package_version="v0.1";status="ERROR";stage="INIT";target="";backup="";checks=[ordered]@{};old_sha256=[ordered]@{};new_sha256=[ordered]@{};next_gate="";error="";prod_enabled=$false}
function Save-Report {
  New-Item -ItemType Directory -Force -Path $Runtime|Out-Null
  ($Report|ConvertTo-Json -Depth 9)|Set-Content -LiteralPath $Record -Encoding UTF8
  $Report|ConvertTo-Json -Depth 9
}
function Hash-Files([string]$Dir) {
  $map=[ordered]@{}
  foreach($f in $Managed) {
    $p=Join-Path $Dir $f
    if(-not(Test-Path -LiteralPath $p -PathType Leaf)){throw "MANAGED_FILE_MISSING:$f"}
    $map[$f]=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()
  }
  return $map
}
function Copy-Managed([string]$From,[string]$To) {
  foreach($f in $Managed) {
    $dst=Join-Path $To $f
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst)|Out-Null
    Copy-Item -LiteralPath (Join-Path $From $f) -Destination $dst -Force
  }
}
function Assert-NoReparse([string]$Path) {
  $item=Get-Item -LiteralPath $Path -Force
  if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw "TARGET_REPARSE_DENIED"}
  foreach($part in $Managed) {
    $relative=Split-Path -Parent $part
    if($relative -and $relative -ne ".") {
      $p=Join-Path $Path $relative
      if(Test-Path -LiteralPath $p){
        $i=Get-Item -LiteralPath $p -Force
        if(($i.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw "MANAGED_REPARSE_DENIED"}
      }
    }
  }
}
function Stop-ScopedProcesses([string]$Target) {
  # Stop only CEREBRO scripts under this exact installation; preserve unrelated 8765.
  $prefix=[IO.Path]::GetFullPath($Target).TrimEnd('\')+"\"
  foreach($p in @(Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'")) {
    $cmd=[string]$p.CommandLine
    if($cmd -notmatch '(?i)(CerebroBrowserBridgeService|CerebroBrowserTransport)\.ps1'){continue}
    if($cmd.IndexOf($prefix,[StringComparison]::OrdinalIgnoreCase) -lt 0){continue}
    if($p.ProcessId -ne $PID){Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue}
  }
}
function Start-Existing([string]$Target) {
  $launcher=Join-Path $Target "Start-CerebroBrowserBridge.ps1"
  if(-not(Test-Path -LiteralPath $launcher)){throw "EXISTING_LAUNCHER_MISSING"}
  $env:CEREBRO_BRIDGE_PORT="8766"
  & $launcher | Out-Null
  $healthy=$false
  foreach($port in 8765..8785) {
    try{
      $h=Invoke-RestMethod -UseBasicParsing -Uri "http://127.0.0.1:$port/health" -TimeoutSec 1
      if($h.service -eq "CEREBRO Browser Bridge" -and $h.service_version -eq "1.4.1" -and
         $h.company_id -eq "fenix" -and $h.environment -eq "LAB" -and
         [bool]$h.paired -and [bool]$h.kill_switch_enabled){$healthy=$true;break}
    }catch{}
  }
  if(-not $healthy){throw "POST_START_HEALTH_NOT_VERIFIED"}
}
function Assert-EqualHashes([string]$Source,[string]$Target) {
  $a=Hash-Files $Source;$b=Hash-Files $Target
  foreach($f in $Managed){if($a[$f] -cne $b[$f]){throw "FILE_HASH_MISMATCH:$f"}}
}
try {
  if($Rollback) {
    if(-not(Test-Path -LiteralPath $Record)){throw "ROLLBACK_STATE_MISSING"}
    $old=Get-Content -Raw -LiteralPath $Record|ConvertFrom-Json
    if(-not $old.backup -or -not $old.target){throw "ROLLBACK_POINTER_MISSING"}
    $Report.stage="RESTORE";$Report.target=[string]$old.target;$Report.backup=[string]$old.backup
    Assert-NoReparse $Report.target
    Stop-ScopedProcesses $Report.target
    Copy-Managed $Report.backup $Report.target
    Assert-EqualHashes $Report.backup $Report.target
    Start-Existing $Report.target
    $Report.status="ROLLED_BACK";$Report.stage="RESTORED";$Report.next_gate="RELOAD_PREVIOUS_EXTENSION"
    Save-Report;exit 0
  }
  if(Test-Path -LiteralPath $Record) {
    $last=Get-Content -Raw -LiteralPath $Record|ConvertFrom-Json
    if($last.status -in @("PARTIAL","INSTALLED","ERROR") -and $last.backup -and
       (Test-Path -LiteralPath ([string]$last.backup))){
      throw "PREVIOUS_SNAPSHOT_EXISTS_USE_ROLLBACK_OR_REVIEW"
    }
  }
  $Report.stage="INVENTORY"
  $recovery=Join-Path $Runtime "recovery-v1.6.2.json"
  if(-not(Test-Path -LiteralPath $recovery)){throw "V162_RECORD_MISSING"}
  $prior=Get-Content -Raw -LiteralPath $recovery|ConvertFrom-Json
  $Target=if($TargetDirectory){(Resolve-Path -LiteralPath $TargetDirectory).Path}else{[string]$prior.target}
  if(-not(Test-Path -LiteralPath $Target -PathType Container)){throw "BRIDGE_TARGET_MISSING"}
  Assert-NoReparse $Target
  $Report.target=$Target
  $health=$null
  foreach($port in 8765..8785){
    try{
      $h=Invoke-RestMethod -UseBasicParsing -Uri "http://127.0.0.1:$port/health" -TimeoutSec 1
      if($h.service -eq "CEREBRO Browser Bridge" -and $h.service_version -eq "1.4.1" -and
         $h.company_id -eq "fenix" -and $h.environment -eq "LAB" -and
         $h.version -eq "v0" -and -not [bool]$h.prod_allowed){$health=$h;break}
    }catch{}
  }
  if(-not $health){throw "TRUSTED_LAB_BRIDGE_NOT_FOUND"}
  if(-not [bool]$health.paired -or -not [bool]$health.kill_switch_enabled){throw "BRIDGE_NOT_SAFE"}
  if(-not(Test-Path -LiteralPath (Join-Path $Runtime "transport-local-key-1.4.1.txt")) -or
     -not(Test-Path -LiteralPath (Join-Path $Runtime "transport-1.4.1.json"))){throw "EXISTING_CREDENTIALS_NOT_FOUND"}
  $Report.checks.existing_bridge=$true
  $Report.checks.credentials_preserved=$true
  $Report.stage="VERIFY_PAYLOAD"
  $Payload=Join-Path $Root "payload"
  $manifestFile=Join-Path $Root "manifest-sha256.json"
  if(-not(Test-Path -LiteralPath $manifestFile)){throw "PACKAGE_MANIFEST_MISSING"}
  $manifest=Get-Content -Raw -LiteralPath $manifestFile|ConvertFrom-Json
  foreach($f in $Managed) {
    $p=Join-Path $Payload $f
    if(-not(Test-Path -LiteralPath $p)){throw "PAYLOAD_FILE_MISSING:$f"}
    $expected=($manifest.files|Where-Object {$_.path -ceq ("payload/"+$f.Replace('\','/'))}|Select-Object -First 1).sha256
    if(-not $expected -or (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -cne [string]$expected){
      throw "PACKAGE_HASH_MISMATCH:$f"
    }
  }
  $m=Get-Content -Raw -LiteralPath (Join-Path $Payload "chrome_extension_v1_4_1\manifest.json")|ConvertFrom-Json
  $w=Get-Content -Raw -LiteralPath (Join-Path $Payload "chrome_extension_v1_4_1\service_worker.js")
  $bs=Get-Content -Raw -LiteralPath (Join-Path $Payload "CerebroBrowserBridgeService.ps1")
  $ts=Get-Content -Raw -LiteralPath (Join-Path $Payload "CerebroBrowserTransport.ps1")
  if($m.version -ne "1.7.0" -or $w -notmatch 'EXTENSION_VERSION = "1\.7\.0"' -or
     $w -notmatch 'EXPECTED_SERVICE_VERSION = "1\.4\.1"' -or
     $bs -notmatch '\$ServiceVersion = "1\.4\.1"' -or
     $ts -notmatch '\$TransportVersion = "1\.4\.1"'){throw "CROSS_VERSION_CONTRACT_MISMATCH"}
  $Report.checks.payload_sha256=$true
  $Report.checks.cross_version=$true
  $Report.checks.lab_only=$true
  $Report.stage="SNAPSHOT"
  $Backup=Join-Path $Runtime ("accessboot-backup-v0-"+(Get-Date -Format "yyyyMMdd-HHmmss")+"-"+[Guid]::NewGuid().ToString("N").Substring(0,8))
  New-Item -ItemType Directory -Path $Backup|Out-Null
  $Report.backup=$Backup
  $Report.old_sha256=Hash-Files $Target
  Copy-Managed $Target $Backup
  Assert-EqualHashes $Target $Backup
  $Report.checks.backup_hash_verified=$true
  Save-Report|Out-Null
  $Report.stage="INSTALL"
  Stop-ScopedProcesses $Target
  Copy-Managed $Payload $Target
  Assert-EqualHashes $Payload $Target
  $Report.new_sha256=Hash-Files $Target
  $Report.stage="START"
  Start-Existing $Target
  $Report.status="PARTIAL";$Report.stage="INSTALLED"
  $Report.next_gate="RELOAD_EXISTING_EXTENSION_ONCE_THEN_CLOUD_FS_AND_YOUTUBE_ACCEPTANCE"
  Save-Report;exit 0
}catch {
  $Report.error=$_.Exception.Message
  if($Report.backup -and $Report.target -and $Report.stage -in @("INSTALL","START")){
    try{
      Stop-ScopedProcesses $Report.target
      Copy-Managed $Report.backup $Report.target
      Assert-EqualHashes $Report.backup $Report.target
      Start-Existing $Report.target
      $Report.status="ROLLED_BACK";$Report.next_gate="RELOAD_PREVIOUS_EXTENSION"
    }catch{$Report.status="ERROR";$Report.next_gate="MANUAL_RECOVERY_REQUIRED"}
  }
  Save-Report;exit 1
}
