param(
    [string]$TransportScript = (Join-Path $PSScriptRoot 'CerebroBrowserTransport.ps1'),
    [string]$PairingFile = (Join-Path $PSScriptRoot 'PAIRING_ONCE.txt')
)

$ErrorActionPreference = 'Stop'
$base = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { $HOME }
$runtime = Join-Path $base 'CEREBRO\browser-bridge'
New-Item -ItemType Directory -Path $runtime -Force | Out-Null
$reportPath = Join-Path $runtime 'transport-launch-1.4.1.json'
$result = [ordered]@{status='ERROR'; stage='BOOT_START'; pid=$null; port=$null; cloud_transport_status=''; stdout=''; stderr=''; error=''}

function Save-Result {
    $result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    $result | ConvertTo-Json -Depth 4
}
function Health([int]$port) {
    try {
        return Invoke-RestMethod -UseBasicParsing -Uri "http://127.0.0.1:$port/health" -Method Get -TimeoutSec 1
    } catch { return $null }
}
function In-Scope($h) {
    return ($h -and $h.service -eq 'CEREBRO Browser Bridge' -and $h.service_version -eq '1.4.1' -and
        [bool]$h.paired -and $h.company_id -eq 'fenix' -and $h.environment -eq 'LAB' -and $h.version -eq 'v0')
}

try {
    $result.stage = 'BRIDGE_DISCOVERY'
    $bridge = $null
    foreach ($candidate in 8765..8785) {
        $h = Health $candidate
        if ($h -and $h.service -eq 'CEREBRO Browser Bridge' -and $h.service_version -eq '1.4.1') {
            $bridge = $h; $result.port = $candidate; break
        }
    }
    if (-not $bridge) { $result.status = 'BRIDGE_NOT_FOUND'; throw 'BRIDGE_NOT_FOUND' }
    if (-not (In-Scope $bridge)) { $result.status = 'SCOPE_DENIED'; throw 'BRIDGE_SCOPE_DENIED' }
    if (-not (Test-Path -LiteralPath (Join-Path $runtime 'transport-local-key-1.4.1.txt'))) {
        $result.status = 'CREDENTIAL_ERROR'; throw 'TRANSPORT_KEY_FILE_MISSING'
    }
    if (-not (Test-Path -LiteralPath $TransportScript)) { throw 'TRANSPORT_SCRIPT_MISSING' }
    $credential = Join-Path $runtime 'transport-1.4.1.json'
    if (-not (Test-Path -LiteralPath $credential) -and -not (Test-Path -LiteralPath $PairingFile)) {
        $result.status = 'PAIRING_REQUIRED'; throw 'PAIRING_FILE_MISSING'
    }
    $result.stage = 'PROCESS_DISCOVERY'
    $workers = @(Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" | Where-Object {
        $_.CommandLine -and $_.CommandLine.Contains('CerebroBrowserTransport.ps1')
    })
    if ($workers.Count -gt 0) {
        $result.pid = $workers[0].ProcessId
        $result.cloud_transport_status = [string]$bridge.cloud_transport_status
        $result.status = if ($bridge.cloud_transport_status -eq 'ONLINE') { 'ONLINE' } else { 'RUNNING' }
        Save-Result
        exit 0
    }
    $result.stage = 'PROCESS_START'
    $psExe = Join-Path $PSHOME 'powershell.exe'
    if (-not (Test-Path -LiteralPath $psExe)) { $psExe = 'powershell.exe' }
    $transport = (Resolve-Path -LiteralPath $TransportScript).Path
    if ($transport.Contains('"') -or $PairingFile.Contains('"')) { throw 'INVALID_SCRIPT_PATH' }
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $result.stdout = Join-Path $runtime "transport-$stamp.stdout.log"
    $result.stderr = Join-Path $runtime "transport-$stamp.stderr.log"
    $argsLine = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $transport + '" -BridgePort ' + $result.port + ' -PairingFile "' + $PairingFile + '"'
    $worker = Start-Process -FilePath $psExe -ArgumentList $argsLine -WorkingDirectory (Split-Path -Parent $transport) -WindowStyle Hidden -RedirectStandardOutput $result.stdout -RedirectStandardError $result.stderr -PassThru
    $result.pid = $worker.Id
    Start-Sleep -Seconds 2
    $worker.Refresh()
    if ($worker.HasExited) { $result.status = 'EXITED'; throw "WORKER_EXIT_$($worker.ExitCode)" }
    Start-Sleep -Seconds 7
    $worker.Refresh()
    if ($worker.HasExited) { $result.status = 'EXITED'; throw "WORKER_EXIT_$($worker.ExitCode)" }
    $latest = Health $result.port
    $result.cloud_transport_status = [string]$latest.cloud_transport_status
    $result.status = if ($latest.cloud_transport_status -eq 'ONLINE') { 'ONLINE' } elseif ($latest.cloud_transport_status -eq 'ENROLLING') { 'ENROLLED' } else { 'RUNNING' }
    $result.stage = 'OBSERVED'
    Save-Result
} catch {
    $result.error = $_.Exception.Message
    Save-Result
    exit 1
}
