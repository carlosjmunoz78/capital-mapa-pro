param([switch]$Rollback, [string]$TargetDirectory = '')

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$payload = Join-Path $root 'payload'
$base = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { $HOME }
$runtime = Join-Path $base 'CEREBRO\browser-bridge'
New-Item -ItemType Directory -Path $runtime -Force | Out-Null
$statePath = Join-Path $runtime 'recovery-v1.4.2.json'
$files = @('CerebroBrowserTransport.ps1','Start-CerebroBrowserTransport.ps1','Start-CerebroBrowserBridge.ps1','package_manifest_v1_4_1.json')
$result = [ordered]@{record_type='cerebro_browser_transport_recovery';status='ERROR';stage='START';target='';backup='';checks=[ordered]@{};files=@();launcher=$null;acceptance=$null;error=''}

function Get-Sha256([string]$Path) {
    $stream = [System.IO.File]::OpenRead($Path)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return (($sha.ComputeHash($stream) | ForEach-Object { $_.ToString('x2') }) -join '')
    } finally {
        $sha.Dispose()
        $stream.Dispose()
    }
}

function Save-State {
    $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statePath -Encoding UTF8
    $result | ConvertTo-Json -Depth 8
}
function Stop-TransportWorkers {
    $workers = @(Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" | Where-Object {
        $_.CommandLine -and $_.CommandLine.Contains('CerebroBrowserTransport.ps1') -and
        -not $_.CommandLine.Contains('Start-CerebroBrowserTransport.ps1')
    })
    foreach ($worker in $workers) { Stop-Process -Id $worker.ProcessId -Force -ErrorAction Stop }
    return $workers.Count
}
function Restore-Files([string]$target,[string]$backup) {
    foreach ($name in $files) {
        $old = Join-Path $backup $name
        $current = Join-Path $target $name
        if (Test-Path -LiteralPath $old) { Copy-Item -LiteralPath $old -Destination $current -Force }
        elseif (Test-Path -LiteralPath $current) { Remove-Item -LiteralPath $current -Force }
    }
}

try {
    if ($Rollback) {
        if (-not (Test-Path -LiteralPath $statePath)) { throw 'ROLLBACK_STATE_MISSING' }
        $previous = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
        if (-not $previous.target -or -not $previous.backup -or -not (Test-Path -LiteralPath $previous.backup)) { throw 'ROLLBACK_BACKUP_MISSING' }
        [void](Stop-TransportWorkers)
        Restore-Files $previous.target $previous.backup
        $result.target = $previous.target; $result.backup = $previous.backup
        $result.status = 'ROLLED_BACK'; $result.stage = 'RESTORED'
        Save-State; exit 0
    }
    $result.stage = 'INVENTORY'
    if ($TargetDirectory) {
        $target = (Resolve-Path -LiteralPath $TargetDirectory).Path
    } else {
        $roots = @((Split-Path -Parent $root),(Join-Path $env:USERPROFILE 'Downloads'),(Join-Path $env:USERPROFILE 'Desktop'),(Join-Path $env:USERPROFILE 'Documents'))
        $candidates = @()
        foreach ($searchRoot in ($roots | Select-Object -Unique)) {
            if (Test-Path -LiteralPath $searchRoot) {
                $candidates += @(Get-ChildItem -LiteralPath $searchRoot -File -Recurse -Filter 'CerebroBrowserBridgeService.ps1' -ErrorAction SilentlyContinue |
                    Where-Object { $_.FullName -notlike '*\work\repo\*' -and (Test-Path -LiteralPath (Join-Path $_.DirectoryName 'CerebroBrowserTransport.ps1')) })
                if ($candidates.Count -gt 0) { break }
            }
        }
        $found = @($candidates | Sort-Object LastWriteTime -Descending | Select-Object -First 1)
        if ($found.Count -gt 0) { $target = $found[0].DirectoryName }
    }
    if (-not $target) { throw 'EXISTING_PACKAGE_NOT_FOUND' }
    if (-not (Test-Path -LiteralPath (Join-Path $target 'CerebroBrowserBridgeService.ps1'))) { throw 'EXISTING_PACKAGE_NOT_FOUND' }
    $result.target = $target
    $manifest = Get-Content -Raw -LiteralPath (Join-Path $target 'package_manifest_v1_4_1.json') | ConvertFrom-Json
    if ($manifest.service_version -ne '1.4.1' -or $manifest.prod_enabled) { throw 'PACKAGE_SCOPE_DENIED' }
    $result.checks.package_version = $true
    $result.checks.powershell_51 = ($PSVersionTable.PSVersion.Major -eq 5)
    $result.checks.dotnet_http = $true
    $expected = Get-Content -Raw -LiteralPath (Join-Path $root 'payload-sha256.json') | ConvertFrom-Json
    foreach ($name in $files) {
        $actual = Get-Sha256 (Join-Path $payload $name)
        if ($actual -ne [string]$expected.$name) { throw "PAYLOAD_HASH_MISMATCH $name" }
    }
    $result.stage = 'SNAPSHOT'
    $backup = Join-Path $runtime ('recovery-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Path $backup -Force | Out-Null
    $result.backup = $backup
    foreach ($name in $files) {
        $old = Join-Path $target $name
        if (Test-Path -LiteralPath $old) {
            Copy-Item -LiteralPath $old -Destination (Join-Path $backup $name) -Force
            $result.files += [ordered]@{name=$name;previous_sha256=Get-Sha256 $old}
        } else { $result.files += [ordered]@{name=$name;previous_sha256=$null} }
    }
    Save-State | Out-Null
    $result.stage = 'INSTALL'
    $result.checks.old_transport_workers_stopped = Stop-TransportWorkers
    foreach ($name in $files) { Copy-Item -LiteralPath (Join-Path $payload $name) -Destination (Join-Path $target $name) -Force }
    $result.stage = 'START'
    $launchOutput = & (Join-Path $target 'Start-CerebroBrowserTransport.ps1')
    $launch = $launchOutput | ConvertFrom-Json
    $result.launcher = $launch
    if ($launch.status -in @('ERROR','EXITED','SCOPE_DENIED','BRIDGE_NOT_FOUND','CREDENTIAL_ERROR')) { throw "WORKER_LAUNCH_$($launch.status)" }
    $result.stage = 'VERIFY'
    $verifyOutput = & (Join-Path $target 'Verify-CerebroBrowserBridge.ps1')
    $result.acceptance = ($verifyOutput | ConvertFrom-Json)
    $result.status = if ($result.acceptance.status -eq 'GREEN') { 'GREEN' } else { 'PARTIAL' }
    Save-State
    exit 0
} catch {
    $result.error = $_.Exception.Message
    if ($result.backup -and $result.target -and $result.stage -in @('INSTALL','START','VERIFY')) {
        [void](Stop-TransportWorkers)
        Restore-Files $result.target $result.backup
        $result.status = 'ROLLED_BACK'
    }
    Save-State
    exit 1
}
