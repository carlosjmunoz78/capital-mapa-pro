param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1024, 65535)]
    [int]$Port,
    [string]$StatePath = ""
)

$ErrorActionPreference = "Stop"
$ServiceName = "CEREBRO Browser Bridge"
$ServiceVersion = "1.0.0"
$HostAddress = [System.Net.IPAddress]::Loopback

if ([string]::IsNullOrWhiteSpace($StatePath)) {
    $Base = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { $HOME }
    $StatePath = Join-Path $Base "CEREBRO\browser-bridge\state.json"
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

function Read-State {
    $state = Get-DefaultState
    if (Test-Path $StatePath) {
        try {
            $raw = Get-Content -Raw -LiteralPath $StatePath -Encoding UTF8 | ConvertFrom-Json
            foreach ($key in @(
                "device_id","company_id","profile_id","browser_family","environment","version",
                "paired","online","kill_switch_enabled","last_seen_at",
                "cloud_transport_configured","cloud_transport_status",
                "chrome_running","chrome_user_data_dir","chrome_profiles",
                "chrome_last_used_profile","browser_discovery_status"
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
            if ($path -eq "/pair") {
                $form = Parse-Query $query
                $company = [string]$form["company_id"]; $profile = [string]$form["profile_id"]
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
