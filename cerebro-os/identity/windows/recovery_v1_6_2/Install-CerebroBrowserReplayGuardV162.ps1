param([switch]$Rollback,[string]$TargetDirectory="")
$ErrorActionPreference="Stop"
$Root=$PSScriptRoot
$Runtime=Join-Path $env:LOCALAPPDATA "CEREBRO\browser-bridge"
New-Item -ItemType Directory -Force -Path $Runtime | Out-Null
$Record=Join-Path $Runtime "recovery-v1.6.2.json"
$Managed=@("CerebroBrowserBridgeService.ps1","chrome_extension_v1_4_1\manifest.json","chrome_extension_v1_4_1\service_worker.js")
$Report=[ordered]@{record_type="cerebro_browser_replay_guard_recovery";package_version="1.6.2";status="ERROR";stage="INIT";target="";backup="";checks=[ordered]@{};next_gate="";error="";prod_enabled=$false}
function Save-Report { ($Report | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $Record -Encoding UTF8; $Report | ConvertTo-Json -Depth 8 }
function Hash-File([string]$p){(Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant()}
function Stop-Bridge {
  $stopped=0
  foreach($p in @(Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'")) {
    $c=[string]$p.CommandLine
    if ($c -match '(?i)(?:-file|\\)\s*"?[^"]*(CerebroBrowserBridgeService|CerebroBrowserTransport)\.ps1' -and
        $c -notmatch '(?i)Start-CerebroBrowser') {
      Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
      $stopped++
    }
  }
  return $stopped
}
function Restore([string]$Target,[string]$Backup) {
 foreach($name in $Managed){
   $src=Join-Path $Backup $name
   if(-not (Test-Path -LiteralPath $src)){throw "ROLLBACK_FILE_MISSING"}
   Copy-Item -LiteralPath $src -Destination (Join-Path $Target $name) -Force
 }
}
function Launch([string]$Target) {
 $start=Join-Path $Target "Start-CerebroBrowserBridge.ps1"
 if(-not (Test-Path $start)){throw "BRIDGE_LAUNCHER_MISSING"}
 & $start | Out-Null
}
try {
 if ($Rollback) {
   if(-not (Test-Path $Record)){throw "ROLLBACK_STATE_MISSING"}
   $previous=Get-Content -Raw -LiteralPath $Record | ConvertFrom-Json
   if(-not $previous.backup -or -not $previous.target){throw "ROLLBACK_POINTER_MISSING"}
   [void](Stop-Bridge)
   Restore ([string]$previous.target) ([string]$previous.backup)
   Launch ([string]$previous.target)
   $Report.target=[string]$previous.target;$Report.backup=[string]$previous.backup
   $Report.status="ROLLED_BACK";$Report.stage="RESTORED";$Report.next_gate="RELOAD_PREVIOUS_CHROME_EXTENSION"
   Save-Report
   exit 0
 }
 $Report.stage="INVENTORY"
 $prior=if(Test-Path $Record){Get-Content -Raw -LiteralPath $Record | ConvertFrom-Json}else{$null}
 if($prior -and $prior.status -eq "PARTIAL"){throw "PREVIOUS_PATCH_PENDING_ACCEPTANCE"}
 $candidate=if($TargetDirectory){$TargetDirectory}else{
   $previousRecord=Join-Path $Runtime "recovery-v1.6.1.json"
   if(Test-Path $previousRecord){
     $p=Get-Content -Raw -LiteralPath $previousRecord | ConvertFrom-Json
     [string]$p.target
   }else{Join-Path $env:USERPROFILE "Downloads\CEREBRO_BROWSER_BRIDGE_WINDOWS_V1_4_1"}
 }
 if(-not (Test-Path -LiteralPath $candidate)){throw "INSTALLED_BRIDGE_NOT_FOUND"}
 $Target=(Resolve-Path -LiteralPath $candidate).Path
 $Report.target=$Target
 $manifestPath=Join-Path $Target "package_manifest_v1_4_1.json"
 if(-not (Test-Path -LiteralPath $manifestPath)){throw "ORIGINAL_MANIFEST_MISSING"}
 $orig=Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
 if($orig.service_version -ne "1.4.1" -or [bool]$orig.prod_enabled){throw "BRIDGE_SCOPE_DENIED"}
 $current=Get-Content -Raw -LiteralPath (Join-Path $Target "chrome_extension_v1_4_1\manifest.json") | ConvertFrom-Json
 if($current.version -ne "1.6.1"){throw "REQUIRES_INSTALLED_V161"}
 foreach($name in $Managed){if(-not(Test-Path -LiteralPath (Join-Path $Target $name))){throw "INSTALLED_FILE_MISSING"}}
 $Report.checks.existing_v161=$true
 $Report.checks.prod_disabled=$true
 $Report.stage="VERIFY_PAYLOAD"
 $expected=Get-Content -Raw -LiteralPath (Join-Path $Root "payload-sha256.json") | ConvertFrom-Json
 foreach($name in $Managed){
  $src=Join-Path (Join-Path $Root "payload") $name
  $key=$name.Replace("\","/")
  if(-not(Test-Path -LiteralPath $src) -or (Hash-File $src) -ne [string]$expected.$key){throw "PAYLOAD_HASH_MISMATCH"}
 }
 $patch=Get-Content -Raw -LiteralPath (Join-Path $Root "payload\chrome_extension_v1_4_1\manifest.json") | ConvertFrom-Json
 if($patch.version -ne "1.6.2" -or @($patch.host_permissions).Count -ne 2 -or
   "http://127.0.0.1/*" -notin @($patch.host_permissions) -or
   "https://example.com/*" -notin @($patch.host_permissions) -or
   "storage" -notin @($patch.permissions)){throw "EXTENSION_SCOPE_DENIED"}
 $Report.checks.hashes=$true;$Report.checks.host_scope=$true
 $Report.stage="SNAPSHOT"
 $Backup=Join-Path $Runtime ("recovery-backup-v162-"+(Get-Date -Format "yyyyMMdd-HHmmss"))
 New-Item -ItemType Directory -Force -Path $Backup | Out-Null
 $Report.backup=$Backup
 foreach($name in $Managed){
  $dest=Join-Path $Backup $name
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
  Copy-Item -LiteralPath (Join-Path $Target $name) -Destination $dest -Force
 }
 Save-Report | Out-Null
 $Report.stage="INSTALL"
 $Report.checks.stopped_bridge_processes=Stop-Bridge
 foreach($name in $Managed){Copy-Item -LiteralPath (Join-Path (Join-Path $Root "payload") $name) -Destination (Join-Path $Target $name) -Force}
 $Report.stage="START"
 Launch $Target
 $Report.stage="VERIFY"
 # IMPORTANT: Verify-CerebroBrowserBridge.ps1 intentionally exits 2 while Chrome
 # is disabled; do not invoke it from the installer or use extension/transport
 # health as a prerequisite for a safe file upgrade.
 # Start-CerebroBrowserBridge.ps1 can take >10 seconds to bootstrap transport.
 # Only the exact trusted Fenix LAB bridge is an installation health gate.
 $health=$null
 $observedPort=$null
 for($attempt=1;$attempt -le 45;$attempt++){
   foreach($port in @(8765)+@(8766..8785)){
     # First port should respond immediately once launched. Avoid scanning the
     # full range on every second when the expected listener is not yet ready.
     if($port -ne 8765 -and $attempt % 5 -ne 0){continue}
     try {
       $candidate=Invoke-RestMethod -UseBasicParsing -Uri ("http://127.0.0.1:"+$port+"/health") -Method Get -TimeoutSec 1
       if($candidate.status -eq "GREEN" -and $candidate.service -eq "CEREBRO Browser Bridge" -and
          $candidate.service_version -eq "1.4.1" -and $candidate.company_id -eq "fenix" -and
          $candidate.environment -eq "LAB" -and $candidate.version -eq "v0" -and
          [bool]$candidate.paired -and [bool]$candidate.kill_switch_enabled){
         $health=$candidate;$observedPort=$port
         break
       }
     }catch {}
   }
   if($health){
     $Report.checks.verify_attempts=$attempt
     $Report.checks.observed_port=$observedPort
     $Report.checks.transport_at_install=[string]$health.cloud_transport_status
     $Report.checks.extension_at_install=[string]$health.extension_status
     break
   }
   Start-Sleep -Seconds 1
 }
 if(-not $health){
   $Report.checks.verify_attempts=45
   throw "LOCAL_BRIDGE_VERIFY_TIMEOUT"
 }
 $Report.checks.local_bridge=$true
 $Report.status="PARTIAL";$Report.next_gate="RELOAD_EXISTING_CHROME_EXTENSION_162_AND_VERIFY_SAME_ID_RECEIPT"
 Save-Report
 exit 0
} catch {
 $Report.error=$_.Exception.Message
 if($Report.stage -in @("INSTALL","START","VERIFY") -and $Report.target -and $Report.backup){
  try {
   [void](Stop-Bridge)
   Restore $Report.target $Report.backup
   Launch $Report.target
   $Report.status="ROLLED_BACK"
   $Report.next_gate="RELOAD_PREVIOUS_CHROME_EXTENSION"
  }catch{$Report.status="ERROR";$Report.next_gate="MANUAL_RECOVERY_REQUIRED"}
 }
 Save-Report
 exit 1
}
