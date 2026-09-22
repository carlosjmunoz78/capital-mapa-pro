param([switch]$Rollback,[string]$TargetDirectory="")
$ErrorActionPreference="Stop"
$Root=$PSScriptRoot
$Runtime=Join-Path $env:LOCALAPPDATA "CEREBRO\browser-bridge"
New-Item -ItemType Directory -Force -Path $Runtime | Out-Null
$Record=Join-Path $Runtime "recovery-v1.6.1.json"
$Managed=@("CerebroBrowserBridgeService.ps1","chrome_extension_v1_4_1\manifest.json","chrome_extension_v1_4_1\service_worker.js")
$Report=[ordered]@{record_type="cerebro_browser_replay_guard_recovery";package_version="1.6.1";status="ERROR";stage="INIT";target="";backup="";checks=[ordered]@{};next_gate="";error="";prod_enabled=$false}
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
   $previousRecord=Join-Path $Runtime "recovery-v1.6.0.json"
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
 if($current.version -ne "1.6.0"){throw "REQUIRES_INSTALLED_V160"}
 foreach($name in $Managed){if(-not(Test-Path -LiteralPath (Join-Path $Target $name))){throw "INSTALLED_FILE_MISSING"}}
 $Report.checks.existing_v160=$true
 $Report.checks.prod_disabled=$true
 $Report.stage="VERIFY_PAYLOAD"
 $expected=Get-Content -Raw -LiteralPath (Join-Path $Root "payload-sha256.json") | ConvertFrom-Json
 foreach($name in $Managed){
  $src=Join-Path (Join-Path $Root "payload") $name
  $key=$name.Replace("\","/")
  if(-not(Test-Path -LiteralPath $src) -or (Hash-File $src) -ne [string]$expected.$key){throw "PAYLOAD_HASH_MISMATCH"}
 }
 $patch=Get-Content -Raw -LiteralPath (Join-Path $Root "payload\chrome_extension_v1_4_1\manifest.json") | ConvertFrom-Json
 if($patch.version -ne "1.6.1" -or @($patch.host_permissions).Count -ne 2 -or
   "http://127.0.0.1/*" -notin @($patch.host_permissions) -or
   "https://example.com/*" -notin @($patch.host_permissions) -or
   "storage" -notin @($patch.permissions)){throw "EXTENSION_SCOPE_DENIED"}
 $Report.checks.hashes=$true;$Report.checks.host_scope=$true
 $Report.stage="SNAPSHOT"
 $Backup=Join-Path $Runtime ("recovery-backup-v161-"+(Get-Date -Format "yyyyMMdd-HHmmss"))
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
 Start-Sleep -Seconds 3
 $Report.stage="VERIFY"
 $verify=Join-Path $Target "Verify-CerebroBrowserBridge.ps1"
 if(-not(Test-Path -LiteralPath $verify)){throw "VERIFY_LAUNCHER_MISSING"}
 $v=& $verify | ConvertFrom-Json
 if(-not $v.checks.service_found -or -not $v.checks.lab_scope -or -not $v.checks.prod_disabled){throw "LOCAL_BRIDGE_VERIFY_FAILED"}
 $Report.checks.local_bridge=$true
 $Report.status="PARTIAL";$Report.next_gate="RELOAD_EXISTING_CHROME_EXTENSION_161_AND_VERIFY_RECEIPT"
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
