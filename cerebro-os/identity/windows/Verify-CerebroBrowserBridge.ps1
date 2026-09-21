param(
    [int]$StartPort = 8765,
    [int]$EndPort = 8785
)

$ErrorActionPreference = "Stop"
$ExpectedService = "CEREBRO Browser Bridge"
$ExpectedVersion = "1.4.1"
$Base = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { $HOME }
$RuntimeDir = Join-Path $Base "CEREBRO\browser-bridge"
$EvidencePath = Join-Path $RuntimeDir "acceptance-$ExpectedVersion.json"
New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null

function Get-BridgeHealth([int]$Port) {
    try {
        $resp = Invoke-RestMethod -UseBasicParsing -Uri "http://127.0.0.1:$Port/health" -Method Get -TimeoutSec 2
        if ($resp.service -eq $ExpectedService -and $resp.service_version -eq $ExpectedVersion -and $resp.status -eq "GREEN") {
            return $resp
        }
    } catch {}
    return $null
}

$port = $null
$health = $null
foreach ($candidate in $StartPort..$EndPort) {
    $candidateHealth = Get-BridgeHealth $candidate
    if ($candidateHealth) {
        $port = $candidate
        $health = $candidateHealth
        break
    }
}

$now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$checks = [ordered]@{
    service_found = $null -ne $health
    service_version = $false
    loopback_only = $true
    paired = $false
    lab_scope = $false
    prod_disabled = $true
    extension_connected = $false
    extension_fresh = $false
    transport_online = $false
    raw_secret_exposed = $false
}

if ($health) {
    $checks["service_version"] = ([string]$health.service_version -eq $ExpectedVersion)
    $checks["paired"] = [bool]$health.paired
    $checks["lab_scope"] = ([string]$health.environment -eq "LAB")
    $checks["prod_disabled"] = ([string]$health.environment -ne "PROD")
    $checks["extension_connected"] = ([string]$health.extension_status -eq "CONNECTED")
    $seen = [int64]$health.extension_last_seen_at
    $age = if ($seen -gt 0) { $now - $seen } else { [int64]::MaxValue }
    $checks["extension_fresh"] = ($age -ge 0 -and $age -le 90)
    $checks["transport_online"] = (
        [bool]$health.cloud_transport_configured -and
        [string]$health.cloud_transport_status -eq "ONLINE"
    )

    foreach ($forbidden in @("password","token","api_key","secret","secret_value","raw_secret","credential_value")) {
        if ($health.PSObject.Properties.Name -contains $forbidden) {
            $checks["raw_secret_exposed"] = $true
        }
    }
}

$blocking = @()
foreach ($name in @("service_found","service_version","paired","lab_scope","prod_disabled","extension_connected","extension_fresh","transport_online")) {
    if (-not [bool]$checks[$name]) { $blocking += $name }
}
if ([bool]$checks["raw_secret_exposed"]) { $blocking += "raw_secret_exposed" }

$status = if ($blocking.Count -eq 0) { "GREEN" } else { "PARTIAL" }
$nextGate = if (-not $checks["service_found"]) {
    "START_LOCAL_BRIDGE"
} elseif (-not $checks["paired"]) {
    "PAIR_LOCAL_DEVICE"
} elseif (-not $checks["extension_connected"] -or -not $checks["extension_fresh"]) {
    "CONNECT_CHROME_EXTENSION"
} elseif (-not $checks["transport_online"]) {
    "PREPROD_DEVICE_ENROLLMENT"
} else {
    "REMOTE_LAB_ROUNDTRIP"
}

$evidence = [ordered]@{
    record_type = "cerebro_browser_bridge_acceptance"
    engine_id = "ACCESSBOOT-001"
    service = $ExpectedService
    service_version = $ExpectedVersion
    environment = if ($health) { [string]$health.environment } else { "LAB" }
    company_id = if ($health) { [string]$health.company_id } else { "" }
    device_id = if ($health) { [string]$health.device_id } else { "" }
    profile_id = if ($health) { [string]$health.profile_id } else { "" }
    port = $port
    checked_at = $now
    status = $status
    checks = $checks
    blocking_checks = @($blocking)
    next_gate = $nextGate
    external_mutation_allowed = $false
    prod_activation_allowed = $false
    secret_value_included = $false
    cost_eur = 0.0
}

($evidence | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $EvidencePath -Encoding UTF8
$evidence | ConvertTo-Json -Depth 6
if ($status -eq "GREEN") { exit 0 }
exit 2
