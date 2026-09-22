param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1024, 65535)]
    [int]$Port,
    [string]$StatePath = "",
    [string]$TransportKey = ""
)

$ErrorActionPreference = "Stop"
$ServiceName = "CEREBRO Browser Bridge"
$ServiceVersion = "1.4.1"
$HostAddress = [System.Net.IPAddress]::Loopback

$Base = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { $HOME }
$RuntimeDir = Join-Path $Base "CEREBRO\browser-bridge"
$LegacyStatePath = Join-Path $RuntimeDir "state.json"

if ([string]::IsNullOrWhiteSpace($StatePath)) {
    $StatePath = Join-Path $RuntimeDir ("state-" + $ServiceVersion + ".json")
}

function Get-DefaultState {
    return [ordered]@{
        record_type = "browser_bridge_local_state"
        service = $ServiceName
        service_version = $ServiceVersion
        device_id = ""
        company_id = ""
        profile_id = ""
        browser_family = "CHROME"
        environment = "LAB"
        version = "v0"
        paired = $false
        online = $true
        kill_switch_enabled = $true
        last_seen_at = 0
        pid = $PID
        cloud_transport_configured = $false
        cloud_transport_status = "NOT_CONFIGURED"
        chrome_running = $false
        chrome_user_data_dir = ""
        chrome_profiles = @()
        chrome_last_used_profile = ""
        browser_discovery_status = "NOT_RUN"
        extension_status = "NOT_CONNECTED"
        extension_id = ""
        extension_version = ""
        extension_last_seen_at = 0
        lab_command_id = ""
        lab_command_action = ""
        lab_command_status = "NONE"
        lab_command_created_at = 0
        lab_command_completed_at = 0
        lab_command_evidence = ""
        lab_command_observed_url = ""
        lab_command_observed_title = ""
        lab_command_page_load_complete = $false
        lab_command_selector = ""
        lab_command_value = ""
        lab_command_observed_value = ""
    }
}

function Get-DeviceId {
    $machine = ""
    try {
        $machine = (Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Cryptography" -Name MachineGuid -ErrorAction Stop).MachineGuid
    } catch {
        $machine = $env:COMPUTERNAME
    }
    if ([string]::IsNullOrWhiteSpace($machine)) { $machine = [Environment]::MachineName }
    $safe = (($machine.ToLowerInvariant()) -replace '[^a-z0-9._-]', '-')
    if ($safe.Length -gt 80) { $safe = $safe.Substring(0, 80) }
    return "desktop-$safe"
}

function Test-ExtensionFresh([System.Collections.IDictionary]$State, [int]$MaxAgeSeconds = 90) {
    if ([string]$State["extension_status"] -ne "CONNECTED") { return $false }
    $seen = [int64]$State["extension_last_seen_at"]
    if ($seen -le 0) { return $false }
    $age = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - $seen
    return ($age -ge 0 -and $age -le $MaxAgeSeconds)
}

function Apply-RuntimeExpiry([System.Collections.IDictionary]$State) {
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    if ([string]$State["extension_status"] -eq "CONNECTED" -and -not (Test-ExtensionFresh $State)) {
        $State["extension_status"] = "STALE"
    }
    if ([string]$State["lab_command_status"] -eq "QUEUED") {
        $created = [int64]$State["lab_command_created_at"]
        if ($created -gt 0 -and ($now - $created) -gt 180) {
            $State["lab_command_status"] = "FAILED"
            $State["lab_command_completed_at"] = $now
            $State["lab_command_evidence"] = "LOCAL_COMMAND_TIMEOUT"
        }
    }
    return $State
}

function Read-State {
    $state = Get-DefaultState

    if (-not (Test-Path $StatePath) -and (Test-Path $LegacyStatePath)) {
        try {
            $legacy = Get-Content -Raw -LiteralPath $LegacyStatePath -Encoding UTF8 | ConvertFrom-Json
            foreach ($key in @(
                "device_id","company_id","profile_id","browser_family","environment","version",
                "paired","chrome_running","chrome_user_data_dir","chrome_profiles",
                "chrome_last_used_profile","browser_discovery_status"
            )) {
                if ($null -ne $legacy.$key) { $state[$key] = $legacy.$key }
            }
        } catch {}
    }

    if (Test-Path $StatePath) {
        try {
            $raw = Get-Content -Raw -LiteralPath $StatePath -Encoding UTF8 | ConvertFrom-Json
            foreach ($key in @(
                "device_id","company_id","profile_id","browser_family","environment","version",
                "paired","online","kill_switch_enabled","last_seen_at",
                "cloud_transport_configured","cloud_transport_status",
                "chrome_running","chrome_user_data_dir","chrome_profiles",
                "chrome_last_used_profile","browser_discovery_status",
                "extension_status","extension_id","extension_version","extension_last_seen_at",
                "lab_command_id","lab_command_action","lab_command_status",
                "lab_command_created_at","lab_command_completed_at","lab_command_evidence",
                "lab_command_observed_url","lab_command_observed_title","lab_command_page_load_complete",
                "lab_command_selector","lab_command_value","lab_command_observed_value"
            )) {
                if ($null -ne $raw.$key) { $state[$key] = $raw.$key }
            }
        } catch { throw "Invalid Browser Bridge local state" }
    }
    if ([string]::IsNullOrWhiteSpace([string]$state["device_id"])) { $state["device_id"] = Get-DeviceId }
    $state["service"] = $ServiceName
    $state["service_version"] = $ServiceVersion
    $state["online"] = $true
    $state["kill_switch_enabled"] = $true
    $state["last_seen_at"] = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $state["pid"] = $PID
    $state = Apply-RuntimeExpiry $state
    return $state
}

function Write-State([System.Collections.IDictionary]$State) {
    $dir = Split-Path -Parent $StatePath
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $tmp = "$StatePath.tmp"
    ($State | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath $tmp -Encoding UTF8
    Move-Item -LiteralPath $tmp -Destination $StatePath -Force
}

function Html([object]$Value) { return [System.Net.WebUtility]::HtmlEncode([string]$Value) }
function UrlDecode([string]$Value) { return [System.Net.WebUtility]::UrlDecode(($Value -replace '\+', ' ')) }

function Parse-Query([string]$Query) {
    $result = @{}
    if ([string]::IsNullOrWhiteSpace($Query)) { return $result }
    foreach ($part in $Query.TrimStart('?').Split('&')) {
        if ([string]::IsNullOrWhiteSpace($part)) { continue }
        $pair = $part.Split('=', 2)
        $key = UrlDecode $pair[0]
        $value = if ($pair.Count -gt 1) { UrlDecode $pair[1] } else { "" }
        $result[$key] = $value
    }
    return $result
}

function Public-State([System.Collections.IDictionary]$State) {
    return [ordered]@{
        service = $ServiceName
        service_version = $ServiceVersion
        device_id = $State["device_id"]
        company_id = $State["company_id"]
        profile_id = $State["profile_id"]
        browser_family = $State["browser_family"]
        environment = $State["environment"]
        version = $State["version"]
        paired = [bool]$State["paired"]
        online = [bool]$State["online"]
        kill_switch_enabled = [bool]$State["kill_switch_enabled"]
        last_seen_at = [int64]$State["last_seen_at"]
        cloud_transport_configured = [bool]$State["cloud_transport_configured"]
        cloud_transport_status = $State["cloud_transport_status"]
        chrome_running = [bool]$State["chrome_running"]
        chrome_user_data_dir = $State["chrome_user_data_dir"]
        chrome_profiles = @($State["chrome_profiles"])
        chrome_last_used_profile = $State["chrome_last_used_profile"]
        browser_discovery_status = $State["browser_discovery_status"]
        extension_status = $State["extension_status"]
        extension_id = $State["extension_id"]
        extension_version = $State["extension_version"]
        extension_last_seen_at = [int64]$State["extension_last_seen_at"]
        lab_command_id = $State["lab_command_id"]
        lab_command_action = $State["lab_command_action"]
        lab_command_status = $State["lab_command_status"]
        lab_command_created_at = [int64]$State["lab_command_created_at"]
        lab_command_completed_at = [int64]$State["lab_command_completed_at"]
        lab_command_evidence = $State["lab_command_evidence"]
        lab_command_observed_url = $State["lab_command_observed_url"]
        lab_command_observed_title = $State["lab_command_observed_title"]
        lab_command_page_load_complete = [bool]$State["lab_command_page_load_complete"]
        lab_command_observed_value = $State["lab_command_observed_value"]
    }
}

function Get-ChromeUserDataDir {
    if ($env:CEREBRO_CHROME_USER_DATA_DIR) {
        return $env:CEREBRO_CHROME_USER_DATA_DIR
    }
    if ($env:LOCALAPPDATA) {
        return (Join-Path $env:LOCALAPPDATA "Google\Chrome\User Data")
    }
    return ""
}

function Discover-Chrome([System.Collections.IDictionary]$State) {
    $userData = Get-ChromeUserDataDir
    $profiles = @()
    $lastUsed = ""

    try {
        $State["chrome_running"] = @((Get-Process chrome -ErrorAction SilentlyContinue)).Count -gt 0
    } catch {
        $State["chrome_running"] = $false
    }

    $State["chrome_user_data_dir"] = $userData
    if ([string]::IsNullOrWhiteSpace($userData) -or -not (Test-Path $userData)) {
        $State["chrome_profiles"] = @()
        $State["chrome_last_used_profile"] = ""
        $State["browser_discovery_status"] = "CHROME_USER_DATA_NOT_FOUND"
        return $State
    }

    $localStatePath = Join-Path $userData "Local State"
    if (Test-Path $localStatePath) {
        try {
            $localState = Get-Content -Raw -LiteralPath $localStatePath -Encoding UTF8 | ConvertFrom-Json
            if ($localState.profile.last_used) {
                $lastUsed = [string]$localState.profile.last_used
            }
            if ($localState.profile.info_cache) {
                foreach ($prop in $localState.profile.info_cache.PSObject.Properties) {
                    $directory = [string]$prop.Name
                    $displayName = [string]$prop.Value.name
                    $profiles += [ordered]@{
                        profile_directory = $directory
                        display_name = $displayName
                        directory_exists = [bool](Test-Path (Join-Path $userData $directory))
                    }
                }
            }
        } catch {
            $State["browser_discovery_status"] = "LOCAL_STATE_PARSE_FAILED"
            $State["chrome_profiles"] = @()
            $State["chrome_last_used_profile"] = ""
            return $State
        }
    }

    if ($profiles.Count -eq 0) {
        foreach ($candidate in @("Default") + @(Get-ChildItem -LiteralPath $userData -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "Profile *" } | Select-Object -ExpandProperty Name)) {
            if ([string]::IsNullOrWhiteSpace([string]$candidate)) { continue }
            $profiles += [ordered]@{
                profile_directory = [string]$candidate
                display_name = [string]$candidate
                directory_exists = [bool](Test-Path (Join-Path $userData $candidate))
            }
        }
    }

    $State["chrome_profiles"] = @($profiles)
    $State["chrome_last_used_profile"] = $lastUsed
    $State["browser_discovery_status"] = if ($profiles.Count -gt 0) { "GREEN" } else { "NO_PROFILES_FOUND" }
    return $State
}

function Canonicalize-ProfileId([System.Collections.IDictionary]$State, [string]$Requested) {
    if ([string]::IsNullOrWhiteSpace($Requested)) { return $Requested }
    foreach ($item in @($State["chrome_profiles"])) {
        try {
            $candidate = [string]$item.profile_directory
            if (-not [string]::IsNullOrWhiteSpace($candidate) -and $candidate.Equals($Requested, [System.StringComparison]::OrdinalIgnoreCase)) {
                return $candidate
            }
        } catch {}
    }
    $lastUsed = [string]$State["chrome_last_used_profile"]
    if (-not [string]::IsNullOrWhiteSpace($lastUsed) -and $lastUsed.Equals($Requested, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $lastUsed
    }
    return $Requested
}

function Render-Page([System.Collections.IDictionary]$State, [string]$Message = "") {
    $messageHtml = if ($Message) { "<p><strong>$(Html $Message)</strong></p>" } else { "" }
    $rows = ""
    foreach ($entry in (Public-State $State).GetEnumerator()) {
        $rows += "<tr><td>$(Html $entry.Key)</td><td>$(Html $entry.Value)</td></tr>"
    }
    $company = if ($State["company_id"]) { $State["company_id"] } else { "fenix" }
    $profile = if ($State["profile_id"]) { $State["profile_id"] } else { "chrome-default" }
    $version = if ($State["version"]) { $State["version"] } else { "v0" }

    return @"
<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>CEREBRO Browser Bridge</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{font-family:Arial,sans-serif;background:#111;color:#eee;margin:0;padding:32px}
main{max-width:760px;margin:auto;background:#1c1c1c;padding:24px;border-radius:12px}
h1{margin-top:0} label{display:block;margin-top:12px}
input,select{width:100%;padding:10px;margin-top:4px;box-sizing:border-box}
button{margin-top:18px;padding:12px 18px;font-weight:700}
table{width:100%;margin-top:24px;border-collapse:collapse}
td{padding:7px;border-bottom:1px solid #333}.ok{color:#9be28f}.warn{color:#ffcf70}
</style></head><body><main>
<h1>CEREBRO Browser Bridge</h1><p class="ok">Servicio local activo en este PC.</p>
$messageHtml
<form method="get" action="/pair">
<label>Empresa <input name="company_id" value="$(Html $company)"></label>
<label>Perfil del navegador <input name="profile_id" value="$(Html $profile)"></label>
<label>Navegador <select name="browser_family"><option>CHROME</option><option>EDGE</option></select></label>
<label>Entorno <select name="environment"><option>LAB</option><option>PREPROD</option></select></label>
<label>Version <input name="version" value="$(Html $version)"></label>
<button type="submit">Emparejar este PC</button></form>
<p><a href="/discover">Detectar perfiles de Chrome en este PC</a></p>
<p>Extension Chrome: <strong>$(Html $State["extension_status"])</strong></p>
<p><a href="/lab/queue-test">Encolar prueba LAB local</a></p>
<table>$rows</table>
<p class="warn">No guarda contrasenas ni tokens. El transporte cloud permanece cerrado hasta validarlo explicitamente.</p>
</main></body></html>
"@
}

function Send-Response($Stream, [int]$Status, [string]$ContentType, [string]$Body) {
    $statusText = switch ($Status) { 200 { "OK" } 400 { "Bad Request" } 404 { "Not Found" } default { "Error" } }
    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($Body)
    $crlf = [string][char]13 + [string][char]10
    $header = "HTTP/1.1 $Status $statusText${crlf}Content-Type: $ContentType${crlf}Content-Length: $($bodyBytes.Length)${crlf}Cache-Control: no-store${crlf}X-Content-Type-Options: nosniff${crlf}X-Frame-Options: DENY${crlf}Connection: close${crlf}${crlf}"
    $headerBytes = [System.Text.Encoding]::ASCII.GetBytes($header)
    $Stream.Write($headerBytes, 0, $headerBytes.Length)
    $Stream.Write($bodyBytes, 0, $bodyBytes.Length)
    $Stream.Flush()
}

$state = Read-State
Write-State $state
$listener = [System.Net.Sockets.TcpListener]::new($HostAddress, $Port)
$listener.Start()

[Console]::Out.WriteLine((@{
    status = "READY"; service = $ServiceName; version = $ServiceVersion; host = "127.0.0.1"; port = $Port
    state_path = $StatePath; prod_enabled = $false; raw_secret_storage = $false
} | ConvertTo-Json -Compress))
[Console]::Out.Flush()

try {
    while ($true) {
        $client = $listener.AcceptTcpClient()
        try {
            $stream = $client.GetStream()
            $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::ASCII, $false, 4096, $true)
            $requestLine = $reader.ReadLine()
            if ([string]::IsNullOrWhiteSpace($requestLine)) {
                Send-Response $stream 400 "application/json; charset=utf-8" '{"error":"bad_request"}'
                continue
            }
            while ($true) {
                $line = $reader.ReadLine()
                if ($null -eq $line -or $line -eq "") { break }
            }
            $parts = $requestLine.Split(' ')
            if ($parts.Count -lt 2 -or $parts[0] -ne "GET") {
                Send-Response $stream 400 "application/json; charset=utf-8" '{"error":"get_only"}'
                continue
            }
            $target = $parts[1]; $path = $target; $query = ""
            $q = $target.IndexOf('?')
            if ($q -ge 0) { $path = $target.Substring(0, $q); $query = $target.Substring($q + 1) }

            $state = Read-State
            if ($path -eq "/health") {
                Write-State $state
                $payload = [ordered]@{ status = "GREEN" }
                foreach ($entry in (Public-State $state).GetEnumerator()) { $payload[$entry.Key] = $entry.Value }
                Send-Response $stream 200 "application/json; charset=utf-8" ($payload | ConvertTo-Json -Compress)
                continue
            }
            if ($path -eq "/discover") {
                $state = Discover-Chrome $state
                Write-State $state
                Send-Response $stream 200 "text/html; charset=utf-8" (Render-Page $state "Deteccion local de Chrome completada.")
                continue
            }
            if ($path -eq "/bootstrap/fenix-lab") {
                $form = Parse-Query $query
                $providedKey = [string]$form["transport_key"]
                if ([string]::IsNullOrWhiteSpace($TransportKey) -or $providedKey -ne $TransportKey) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"TRANSPORT_KEY_MISMATCH"}'
                    continue
                }

                $state = Discover-Chrome $state
                $selectedProfile = ""
                $currentProfile = [string]$state["profile_id"]
                foreach ($item in @($state["chrome_profiles"])) {
                    $candidate = [string]$item.profile_directory
                    if (-not [string]::IsNullOrWhiteSpace($candidate) -and
                        -not [string]::IsNullOrWhiteSpace($currentProfile) -and
                        $candidate.Equals($currentProfile,[System.StringComparison]::OrdinalIgnoreCase)) {
                        $selectedProfile = $candidate
                        break
                    }
                }
                if ([string]::IsNullOrWhiteSpace($selectedProfile)) {
                    $lastUsed = [string]$state["chrome_last_used_profile"]
                    if (-not [string]::IsNullOrWhiteSpace($lastUsed)) {
                        $selectedProfile = Canonicalize-ProfileId $state $lastUsed
                    }
                }
                if ([string]::IsNullOrWhiteSpace($selectedProfile) -and @($state["chrome_profiles"]).Count -gt 0) {
                    $selectedProfile = [string]$state["chrome_profiles"][0].profile_directory
                }
                if ([string]::IsNullOrWhiteSpace($selectedProfile)) {
                    Write-State $state
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"PILOT_PROFILE_NOT_FOUND"}'
                    continue
                }

                # Physical device identity for the Fenix pilot is derived from this Windows machine,
                # never inherited from another company's legacy Browser Bridge state.
                $state["device_id"] = Get-DeviceId
                $state["company_id"] = "fenix"
                $state["profile_id"] = $selectedProfile
                $state["browser_family"] = "CHROME"
                $state["environment"] = "LAB"
                $state["version"] = "v0"
                $state["paired"] = $true
                $state["online"] = $true
                $state["kill_switch_enabled"] = $true
                $state["cloud_transport_configured"] = $false
                $state["cloud_transport_status"] = "NOT_CONFIGURED"
                $state["extension_status"] = "NOT_CONNECTED"
                $state["extension_id"] = ""
                $state["extension_last_seen_at"] = 0
                $state["lab_command_id"] = ""
                $state["lab_command_action"] = ""
                $state["lab_command_status"] = "NONE"
                $state["lab_command_created_at"] = 0
                $state["lab_command_completed_at"] = 0
                $state["lab_command_evidence"] = ""
                $state["last_seen_at"] = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
                Write-State $state

                $payload = [ordered]@{
                    status = "GREEN"
                    decision = "FENIX_LAB_PILOT_BOOTSTRAPPED"
                    company_id = $state["company_id"]
                    device_id = $state["device_id"]
                    profile_id = $state["profile_id"]
                    environment = $state["environment"]
                    version = $state["version"]
                    browser_discovery_status = $state["browser_discovery_status"]
                    external_mutation_allowed = $false
                    prod_activation_allowed = $false
                    secret_value_included = $false
                }
                Send-Response $stream 200 "application/json; charset=utf-8" ($payload | ConvertTo-Json -Compress)
                continue
            }
            if ($path -eq "/transport/status") {
                $form = Parse-Query $query
                $providedKey = [string]$form["transport_key"]
                $status = ([string]$form["status"]).ToUpperInvariant()
                if ([string]::IsNullOrWhiteSpace($TransportKey) -or $providedKey -ne $TransportKey) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"TRANSPORT_KEY_MISMATCH"}'
                    continue
                }
                if ($status -notin @("ENROLLING","ONLINE","ERROR","OFFLINE")) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"TRANSPORT_STATUS_INVALID"}'
                    continue
                }
                $state["cloud_transport_configured"] = $status -eq "ONLINE"
                $state["cloud_transport_status"] = $status
                Write-State $state
                Send-Response $stream 200 "application/json; charset=utf-8" '{"status":"GREEN","decision":"TRANSPORT_STATUS_ACCEPTED"}'
                continue
            }
            if ($path -eq "/cloud/enqueue") {
                $form = Parse-Query $query
                $providedKey = [string]$form["transport_key"]
                $commandId = [string]$form["command_id"]
                $action = ([string]$form["action"]).ToUpperInvariant()
                $operatorActions = @("OPERATOR_CLICK","OPERATOR_TYPE","OPERATOR_SELECT","OPERATOR_READ")
                $selector = [string]$form["selector"]
                $value = [string]$form["value"]
                if ([string]::IsNullOrWhiteSpace($TransportKey) -or $providedKey -ne $TransportKey) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"TRANSPORT_KEY_MISMATCH"}'
                    continue
                }
                if (-not [bool]$state["paired"] -or [string]$state["environment"] -ne "LAB" -or -not (Test-ExtensionFresh $state)) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"LOCAL_EXECUTOR_NOT_READY"}'
                    continue
                }
                if ([string]::IsNullOrWhiteSpace($commandId) -or $action -notin (@("OPEN_LOCAL_TEST_PAGE","READ_ONLY_PAGE_METADATA") + $operatorActions)) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"REMOTE_ACTION_DENIED"}'
                    continue
                }
                if ([string]$state["lab_command_id"] -eq $commandId -and [string]$state["lab_command_status"] -eq "COMPLETED") {
                    Send-Response $stream 200 "application/json; charset=utf-8" '{"status":"GREEN","decision":"IDEMPOTENT_REPLAY_SUPPRESSED"}'
                    continue
                }
                if ([string]$state["lab_command_status"] -eq "QUEUED" -and [string]$state["lab_command_id"] -ne $commandId) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"LOCAL_COMMAND_BUSY"}'
                    continue
                }
                if ($action -in $operatorActions) {
                    $allowedSelector = switch ($action) {
                        "OPERATOR_CLICK" { "#cerebro-button" }
                        "OPERATOR_TYPE" { "#cerebro-input" }
                        "OPERATOR_SELECT" { "#cerebro-select" }
                        "OPERATOR_READ" { "#cerebro-output" }
                    }
                    $invalidType = ($action -eq "OPERATOR_TYPE" -and
                        ($value.Length -lt 1 -or $value.Length -gt 64 -or
                         $value -cnotmatch "^[a-zA-Z0-9 _.-]+$"))
                    $invalidSelect = ($action -eq "OPERATOR_SELECT" -and
                        $value -cnotin @("alpha","beta"))
                    $invalidEmpty = ($action -in @("OPERATOR_CLICK","OPERATOR_READ") -and
                        $value.Length -ne 0)
                    if ([string]$state["extension_version"] -notin @("1.6.0","1.6.1") -or
                        $selector -cne $allowedSelector -or $invalidType -or
                        $invalidSelect -or $invalidEmpty) {
                        Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"OPERATOR_FIXTURE_SCOPE_DENIED"}'
                        continue
                    }
                }
                if ($action -eq "READ_ONLY_PAGE_METADATA" -and
                    [string]$state["extension_version"] -notin @("1.5.0","1.6.0","1.6.1")) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"METADATA_EXTENSION_UPGRADE_REQUIRED"}'
                    continue
                }
                $state["lab_command_id"] = $commandId
                $state["lab_command_action"] = $action
                $state["lab_command_selector"] = if ($action -in $operatorActions) { $selector } else { "" }
                $state["lab_command_value"] = if ($action -in $operatorActions) { $value } else { "" }
                $state["lab_command_observed_value"] = ""
                $state["lab_command_status"] = "QUEUED"
                $state["lab_command_created_at"] = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
                $state["lab_command_completed_at"] = 0
                $state["lab_command_evidence"] = ""
                $state["lab_command_observed_url"] = ""
                $state["lab_command_observed_title"] = ""
                $state["lab_command_page_load_complete"] = $false
                Write-State $state
                Send-Response $stream 200 "application/json; charset=utf-8" '{"status":"GREEN","decision":"REMOTE_COMMAND_ENQUEUED"}'
                continue
            }
            if ($path -eq "/lab/operator-fixture") {
                if ([string]$state["environment"] -ne "LAB" -or -not [bool]$state["paired"]) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"LAB_ONLY"}'
                    continue
                }
                $fixture = '<!doctype html><html><head><meta charset="utf-8"><title>CEREBRO Operator LAB Fixture</title></head><body><h1>CEREBRO Operator LAB Fixture</h1><input id="cerebro-input" maxlength="64"><select id="cerebro-select"><option value="alpha">alpha</option><option value="beta">beta</option></select><button id="cerebro-button" onclick="document.querySelector('' #cerebro-output'').textContent=''CLICKED''">Click</button><output id="cerebro-output">READY</output></body></html>'
                $fixture = $fixture.Replace("' #cerebro-output'", "'#cerebro-output'")
                Send-Response $stream 200 "text/html; charset=utf-8" $fixture
                continue
            }
            if ($path -eq "/lab/test") {
                $form = Parse-Query $query
                $commandId = [string]$form["command_id"]
                $body = "<!doctype html><html><head><meta charset='utf-8'><title>CEREBRO LAB TEST</title></head><body><h1>CEREBRO LAB TEST</h1><p>Pagina local de prueba. Sin mutacion externa.</p><p>command_id=$(Html $commandId)</p></body></html>"
                Send-Response $stream 200 "text/html; charset=utf-8" $body
                continue
            }
            if ($path -eq "/lab/queue-test") {
                if (-not [bool]$state["paired"] -or [string]$state["environment"] -ne "LAB" -or -not (Test-ExtensionFresh $state)) {
                    Send-Response $stream 400 "text/html; charset=utf-8" (Render-Page $state "LAB no listo: requiere paired + LAB + extension CONNECTED.")
                    continue
                }
                $commandId = "lab-" + [Guid]::NewGuid().ToString("N")
                $state["lab_command_id"] = $commandId
                $state["lab_command_action"] = "OPEN_LOCAL_TEST_PAGE"
                $state["lab_command_status"] = "QUEUED"
                $state["lab_command_created_at"] = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
                $state["lab_command_completed_at"] = 0
                $state["lab_command_evidence"] = ""
                Write-State $state
                Send-Response $stream 200 "text/html; charset=utf-8" (Render-Page $state "Prueba LAB local encolada. La extension la ejecutara sin tocar webs externas.")
                continue
            }
            if ($path -eq "/extension/command") {
                if (-not [bool]$state["paired"] -or [string]$state["environment"] -ne "LAB") {
                    Send-Response $stream 200 "application/json; charset=utf-8" '{"status":"GREEN","decision":"NO_COMMAND"}'
                    continue
                }
                $form = Parse-Query $query
                $extensionId = [string]$form["extension_id"]
                if ([string]::IsNullOrWhiteSpace($extensionId) -or $extensionId -ne [string]$state["extension_id"]) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"EXTENSION_SCOPE_MISMATCH"}'
                    continue
                }
                if ([string]$state["lab_command_status"] -ne "QUEUED") {
                    Send-Response $stream 200 "application/json; charset=utf-8" '{"status":"GREEN","decision":"NO_COMMAND"}'
                    continue
                }
                $action = [string]$state["lab_command_action"]
                if ($action -eq "READ_ONLY_PAGE_METADATA" -and [string]$state["extension_version"] -notin @("1.5.0","1.6.0","1.6.1")) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"METADATA_EXTENSION_REQUIRED"}'
                    continue
                }
                $target = if ($action -in @("OPERATOR_CLICK","OPERATOR_TYPE","OPERATOR_SELECT","OPERATOR_READ")) {
                    "http://127.0.0.1:" + $Port + "/lab/operator-fixture"
                } elseif ($action -eq "READ_ONLY_PAGE_METADATA") {
                    "https://example.com/"
                } else {
                    "http://127.0.0.1:" + $Port + "/lab/test?command_id=" + [Uri]::EscapeDataString([string]$state["lab_command_id"])
                }
                $payload = [ordered]@{
                    status = "GREEN"
                    decision = "LAB_COMMAND_AVAILABLE"
                    command_id = $state["lab_command_id"]
                    action = $state["lab_command_action"]
                    target_url = $target
                    external_mutation_allowed = $false
                    environment = "LAB"
                    company_id = [string]$state["company_id"]
                    selector = [string]$state["lab_command_selector"]
                    value = [string]$state["lab_command_value"]
                }
                Send-Response $stream 200 "application/json; charset=utf-8" ($payload | ConvertTo-Json -Compress)
                continue
            }
            if ($path -eq "/extension/operator-result") {
                $form = Parse-Query $query
                $extensionId = [string]$form["extension_id"]
                $commandId = [string]$form["command_id"]
                $result = ([string]$form["result"]).ToUpperInvariant()
                $observed = [string]$form["observed_value"]
                $action = [string]$state["lab_command_action"]
                if ($extensionId -ne [string]$state["extension_id"] -or $commandId -ne [string]$state["lab_command_id"] -or
                    [string]$state["extension_version"] -notin @("1.6.0","1.6.1") -or
                    $action -notin @("OPERATOR_CLICK","OPERATOR_TYPE","OPERATOR_SELECT","OPERATOR_READ")) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"OPERATOR_RESULT_SCOPE_DENIED"}'
                    continue
                }
                if ([string]$state["lab_command_status"] -in @("COMPLETED","FAILED")) {
                    Send-Response $stream 200 "application/json; charset=utf-8" '{"status":"GREEN","decision":"IDEMPOTENT_REPLAY_SUPPRESSED"}'
                    continue
                }
                if ([string]$state["lab_command_status"] -ne "QUEUED" -or $observed.Length -gt 64 -or $result -notin @("COMPLETED","FAILED")) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"OPERATOR_RESULT_INVALID"}'
                    continue
                }
                $semanticValid = switch ($action) {
                    "OPERATOR_CLICK" { $observed -ceq "CLICKED" }
                    "OPERATOR_TYPE" { $observed -ceq [string]$state["lab_command_value"] }
                    "OPERATOR_SELECT" { $observed -ceq [string]$state["lab_command_value"] }
                    "OPERATOR_READ" { $observed -cin @("READY","CLICKED") }
                    default { $false }
                }
                $ok = $result -eq "COMPLETED" -and $semanticValid -and [string]$form["evidence"] -ceq "LAB_OPERATOR_FIXTURE_VERIFIED"
                $state["lab_command_status"] = if ($ok) { "COMPLETED" } else { "FAILED" }
                $state["lab_command_observed_value"] = if ($ok) { $observed } else { "" }
                $state["lab_command_evidence"] = if ($ok) { "LAB_OPERATOR_FIXTURE_VERIFIED" } else { "LAB_OPERATOR_FIXTURE_FAILED" }
                $state["lab_command_completed_at"] = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
                Write-State $state
                Send-Response $stream 200 "application/json; charset=utf-8" (@{
                    status = if ($ok) { "GREEN" } else { "BLOCKED" }
                    decision = "OPERATOR_RECEIPT_RECORDED"
                    semantic_verified = [bool]$ok
                    external_mutation_performed = $false
                } | ConvertTo-Json -Compress)
                continue
            }
            if ($path -eq "/extension/result") {
                $form = Parse-Query $query
                $extensionId = [string]$form["extension_id"]
                $commandId = [string]$form["command_id"]
                $result = ([string]$form["result"]).ToUpperInvariant()
                $observedUrl = [string]$form["observed_url"]
                $observedTitle = [string]$form["observed_title"]
                $pageLoadComplete = [string]$form["page_load_complete"] -eq "true"
                if ($extensionId -ne [string]$state["extension_id"] -or $commandId -ne [string]$state["lab_command_id"]) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"RESULT_SCOPE_MISMATCH"}'
                    continue
                }
                if ($result -notin @("COMPLETED","FAILED")) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"RESULT_STATUS_INVALID"}'
                    continue
                }
                $currentStatus = [string]$state["lab_command_status"]
                if ($currentStatus -in @("COMPLETED","FAILED")) {
                    if ($currentStatus -eq $result) {
                        Send-Response $stream 200 "application/json; charset=utf-8" '{"status":"GREEN","decision":"IDEMPOTENT_REPLAY_SUPPRESSED"}'
                    } else {
                        Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"RESULT_TERMINAL_CONFLICT"}'
                    }
                    continue
                }
                if ($currentStatus -ne "QUEUED") {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"RESULT_NOT_QUEUED"}'
                    continue
                }
                $action = [string]$state["lab_command_action"]
                if ($action -eq "READ_ONLY_PAGE_METADATA") {
                    $readbackValid = ($observedUrl -ceq "https://example.com/" -and
                                      $observedTitle -ceq "Example Domain" -and
                                      $pageLoadComplete)
                    if ($result -eq "COMPLETED" -and -not $readbackValid) { $result = "FAILED" }
                    $state["lab_command_observed_url"] = if ($readbackValid) { "https://example.com/" } else { "" }
                    $state["lab_command_observed_title"] = if ($readbackValid) { "Example Domain" } else { "" }
                    $state["lab_command_page_load_complete"] = [bool]$readbackValid
                } else {
                    $state["lab_command_observed_url"] = ""
                    $state["lab_command_observed_title"] = ""
                    $state["lab_command_page_load_complete"] = $false
                }
                $state["lab_command_status"] = $result
                $state["lab_command_completed_at"] = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
                $state["lab_command_evidence"] = if ($action -eq "READ_ONLY_PAGE_METADATA") {
                    if ($result -eq "COMPLETED") { "EXAMPLE_DOMAIN_METADATA_VERIFIED" } else { "PAGE_READBACK_FAILED" }
                } else {
                    if ($result -eq "COMPLETED") { "LOCAL_TEST_PAGE_OPENED" } else { "LOCAL_TEST_PAGE_FAILED" }
                }
                Write-State $state
                $payload = [ordered]@{
                    status = if ($result -eq "COMPLETED") { "GREEN" } else { "BLOCKED" }
                    decision = if ($result -eq "COMPLETED") { "LAB_COMMAND_RECEIPT_ACCEPTED" } else { "LAB_COMMAND_FAILED" }
                    command_id = $commandId
                    result = $result
                    evidence = $state["lab_command_evidence"]
                    external_mutation_performed = $false
                }
                Send-Response $stream 200 "application/json; charset=utf-8" ($payload | ConvertTo-Json -Compress)
                continue
            }
            if ($path -eq "/extension/ping") {
                if (-not [bool]$state["paired"] -or [string]$state["environment"] -eq "PROD") {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"BRIDGE_NOT_READY"}'
                    continue
                }
                $form = Parse-Query $query
                $extensionId = [string]$form["extension_id"]
                $extensionVersion = [string]$form["extension_version"]
                if ([string]::IsNullOrWhiteSpace($extensionVersion)) { $extensionVersion = "1.4.1" }
                if ($extensionVersion -notin @("1.4.1","1.5.0","1.6.0","1.6.1")) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"EXTENSION_VERSION_DENIED"}'
                    continue
                }
                if ([string]::IsNullOrWhiteSpace($extensionId) -or $extensionId.Length -gt 128) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"EXTENSION_ID_REQUIRED"}'
                    continue
                }
                if (-not [string]::IsNullOrWhiteSpace([string]$state["extension_id"]) -and
                    [string]$state["extension_id"] -ne $extensionId -and
                    (Test-ExtensionFresh $state)) {
                    Send-Response $stream 400 "application/json; charset=utf-8" '{"status":"BLOCKED","decision":"EXTENSION_ID_CONFLICT"}'
                    continue
                }
                $state["extension_status"] = "CONNECTED"
                $state["extension_id"] = $extensionId
                $state["extension_version"] = $extensionVersion
                $state["extension_last_seen_at"] = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
                Write-State $state
                $payload = [ordered]@{
                    status = "GREEN"
                    decision = "EXTENSION_HEARTBEAT_ACCEPTED"
                    service_version = $ServiceVersion
                    company_id = $state["company_id"]
                    profile_id = $state["profile_id"]
                    environment = $state["environment"]
                    version = $state["version"]
                    external_mutation_allowed = $false
                    cloud_transport_configured = [bool]$state["cloud_transport_configured"]
                }
                Send-Response $stream 200 "application/json; charset=utf-8" ($payload | ConvertTo-Json -Compress)
                continue
            }
            if ($path -eq "/pair") {
                $form = Parse-Query $query
                $company = [string]$form["company_id"]; $profile = [string]$form["profile_id"]
                $profile = Canonicalize-ProfileId $state $profile
                $browser = ([string]$form["browser_family"]).ToUpperInvariant()
                $environment = ([string]$form["environment"]).ToUpperInvariant()
                $version = [string]$form["version"]

                if ([string]::IsNullOrWhiteSpace($company) -or [string]::IsNullOrWhiteSpace($profile) -or [string]::IsNullOrWhiteSpace($version)) {
                    Send-Response $stream 400 "text/html; charset=utf-8" (Render-Page $state "Faltan empresa, perfil o versión.")
                    continue
                }
                if ($browser -notin @("CHROME","EDGE")) {
                    Send-Response $stream 400 "text/html; charset=utf-8" (Render-Page $state "Navegador no permitido.")
                    continue
                }
                if ($environment -notin @("LAB","PREPROD")) {
                    Send-Response $stream 400 "text/html; charset=utf-8" (Render-Page $state "Solo LAB/PREPROD están permitidos.")
                    continue
                }
                $state["company_id"]=$company; $state["profile_id"]=$profile; $state["browser_family"]=$browser
                $state["environment"]=$environment; $state["version"]=$version; $state["paired"]=$true
                $state["online"]=$true; $state["kill_switch_enabled"]=$true
                $state["cloud_transport_configured"]=$false; $state["cloud_transport_status"]="NOT_CONFIGURED"
                $state["last_seen_at"]=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
                Write-State $state
                Send-Response $stream 200 "text/html; charset=utf-8" (Render-Page $state "PC emparejado localmente. Manten CEREBRO activo.")
                continue
            }
            if ($path -eq "/" -or $path -eq "/index.html") {
                Write-State $state
                Send-Response $stream 200 "text/html; charset=utf-8" (Render-Page $state)
                continue
            }
            Send-Response $stream 404 "application/json; charset=utf-8" '{"error":"not_found"}'
        } catch {
            try { Send-Response $stream 400 "application/json; charset=utf-8" '{"error":"request_failed"}' } catch {}
        } finally { $client.Close() }
    }
} finally { $listener.Stop() }
