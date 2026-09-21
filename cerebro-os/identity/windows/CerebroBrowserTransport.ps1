param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1024,65535)]
    [int]$BridgePort,
    [Parameter(Mandatory = $true)]
    [string]$TransportKey,
    [Parameter(Mandatory = $true)]
    [string]$PairingFile
)

$ErrorActionPreference = "Stop"
$TransportVersion = "1.4.1"
$GatewayBase = "https://hnqlnvakzaywtafeiybt.supabase.co/functions/v1/cerebro-device-gateway-preprod"
$BridgeBase = "http://127.0.0.1:$BridgePort"
$Base = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { $HOME }
$RuntimeDir = Join-Path $Base "CEREBRO\browser-bridge"
$CredentialPath = Join-Path $RuntimeDir "transport-$TransportVersion.json"
$LogPath = Join-Path $RuntimeDir "transport-$TransportVersion.log"

$createdNew = $false
$mutex = New-Object System.Threading.Mutex($true, "Local\CEREBROBrowserTransportV141", [ref]$createdNew)
if (-not $createdNew) { exit 0 }

function Log([string]$Message) {
    Add-Content -LiteralPath $LogPath -Value ("$(Get-Date -Format o) " + $Message) -Encoding UTF8
}

function Local-Get([string]$Path) {
    return Invoke-RestMethod -UseBasicParsing -Uri ($BridgeBase + $Path) -Method Get -TimeoutSec 5
}

function Set-LocalTransportStatus([string]$Status) {
    $uri = $BridgeBase + "/transport/status?transport_key=" + [uri]::EscapeDataString($TransportKey) + "&status=" + [uri]::EscapeDataString($Status)
    try { Invoke-RestMethod -UseBasicParsing -Uri $uri -Method Get -TimeoutSec 5 | Out-Null } catch {}
}

function New-Token {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return ([Convert]::ToBase64String($bytes).TrimEnd('=') -replace '\+','-' -replace '/','_')
}

function Sha256([string]$Value) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        return (($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") }) -join "")
    } finally { $sha.Dispose() }
}

function Protect-Token([string]$Token) {
    $secure = ConvertTo-SecureString -String $Token -AsPlainText -Force
    return ConvertFrom-SecureString -SecureString $secure
}

function Unprotect-Token([string]$Cipher) {
    $secure = ConvertTo-SecureString -String $Cipher
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

function Read-Credential {
    if (-not (Test-Path $CredentialPath)) { return $null }
    try {
        $obj = Get-Content -Raw -LiteralPath $CredentialPath -Encoding UTF8 | ConvertFrom-Json
        if (-not $obj.token_dpapi) { return $null }
        return [ordered]@{
            token = Unprotect-Token ([string]$obj.token_dpapi)
            device_id = [string]$obj.device_id
            company_id = [string]$obj.company_id
            environment = [string]$obj.environment
            version = [string]$obj.version
        }
    } catch { return $null }
}

function Save-Credential([string]$Token, $Bridge) {
    $record = [ordered]@{
        record_type = "cerebro_browser_transport_credential"
        transport_version = $TransportVersion
        token_dpapi = Protect-Token $Token
        device_id = [string]$Bridge.device_id
        company_id = [string]$Bridge.company_id
        environment = [string]$Bridge.environment
        version = [string]$Bridge.version
        stored_at = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    }
    ($record | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath $CredentialPath -Encoding UTF8
}

function New-Nonce { return ([Guid]::NewGuid().ToString("N") + [Guid]::NewGuid().ToString("N")) }

function Gateway-Call([string]$Method, [string]$Path, [string]$Token, [object]$Body = $null) {
    $headers = @{
        Authorization = "Bearer $Token"
        "X-CEREBRO-Nonce" = New-Nonce
    }
    $args = @{
        UseBasicParsing = $true
        Uri = ($GatewayBase + $Path)
        Method = $Method
        Headers = $headers
        TimeoutSec = 15
    }
    if ($null -ne $Body) {
        $args["ContentType"] = "application/json"
        $args["Body"] = ($Body | ConvertTo-Json -Depth 10 -Compress)
    }
    return Invoke-RestMethod @args
}

function Ensure-Enrolled($Bridge) {
    $cred = Read-Credential
    if ($cred) { return $cred }

    if (-not (Test-Path $PairingFile)) { throw "PAIRING_FILE_MISSING" }
    $pairCode = (Get-Content -Raw -LiteralPath $PairingFile -Encoding UTF8).Trim()
    if ($pairCode.Length -lt 24) { throw "PAIRING_CODE_INVALID" }

    Set-LocalTransportStatus "ENROLLING"
    $token = New-Token
    $payload = [ordered]@{
        device_id = [string]$Bridge.device_id
        company_id = [string]$Bridge.company_id
        environment = [string]$Bridge.environment
        version = [string]$Bridge.version
        agent_version = "browser-transport-ps-$TransportVersion"
        pair_code = $pairCode
        token_sha256 = Sha256 $token
    }

    $response = Invoke-RestMethod -UseBasicParsing -Uri ($GatewayBase + "/v1/agents/enroll") -Method Post -ContentType "application/json" -Body ($payload | ConvertTo-Json -Compress) -TimeoutSec 15
    if ($response.decision -ne "ENROLLED") { throw "ENROLLMENT_FAILED" }

    Save-Credential $token $Bridge
    Remove-Item -LiteralPath $PairingFile -Force -ErrorAction SilentlyContinue
    Log "ENROLLED device=$($Bridge.device_id) scope=$($Bridge.company_id)/$($Bridge.environment)/$($Bridge.version)"
    return Read-Credential
}

function Validate-Scope($Bridge, $Cred) {
    if ([string]$Bridge.service_version -ne $TransportVersion) { throw "BRIDGE_VERSION_MISMATCH" }
    if (-not [bool]$Bridge.paired) { throw "BRIDGE_NOT_PAIRED" }
    if ([string]$Bridge.company_id -ne "fenix" -or [string]$Bridge.environment -ne "LAB" -or [string]$Bridge.version -ne "v0") { throw "BRIDGE_SCOPE_DENIED" }
    if ($Cred) {
        if ($Cred.device_id -ne [string]$Bridge.device_id -or $Cred.company_id -ne [string]$Bridge.company_id -or $Cred.environment -ne [string]$Bridge.environment -or $Cred.version -ne [string]$Bridge.version) {
            throw "CREDENTIAL_SCOPE_MISMATCH"
        }
    }
}

function Enqueue-Local($Command) {
    $action = [string]$Command.payload.action
    if ($action -ne "OPEN_LOCAL_TEST_PAGE") { throw "REMOTE_ACTION_DENIED" }
    $uri = $BridgeBase + "/cloud/enqueue?transport_key=" + [uri]::EscapeDataString($TransportKey) +
      "&command_id=" + [uri]::EscapeDataString([string]$Command.command_id) +
      "&action=" + [uri]::EscapeDataString($action)
    return Invoke-RestMethod -UseBasicParsing -Uri $uri -Method Get -TimeoutSec 5
}

function Wait-LocalResult([string]$CommandId) {
    for ($i=0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 1
        $h = Local-Get "/health"
        if ([string]$h.lab_command_id -ne $CommandId) { continue }
        if ([string]$h.lab_command_status -in @("COMPLETED","FAILED")) {
            return $h
        }
    }
    throw "LOCAL_RESULT_TIMEOUT"
}

New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null

try {
    $bridge = Local-Get "/health"
    Validate-Scope $bridge $null
    $cred = Ensure-Enrolled $bridge
    Validate-Scope $bridge $cred

    $reconnect = Gateway-Call "POST" "/v1/agents/reconnect" $cred.token ([ordered]@{device_id=$cred.device_id})
    Set-LocalTransportStatus "ONLINE"
    Log "ONLINE queued=$($reconnect.queued_commands)"

    while ($true) {
        try {
            $bridge = Local-Get "/health"
            Validate-Scope $bridge $cred
            $poll = Gateway-Call "GET" ("/v1/agents/poll?device_id=" + [uri]::EscapeDataString($cred.device_id)) $cred.token
            $commands = @($poll.commands)
            if ($commands.Count -eq 0) {
                Set-LocalTransportStatus "ONLINE"
                Start-Sleep -Seconds 10
                continue
            }

            $cmd = $commands[0]
            if ([string]$cmd.company_id -ne $cred.company_id -or [string]$cmd.environment -ne $cred.environment -or [string]$cmd.version -ne $cred.version -or [string]$cmd.device_id -ne $cred.device_id) {
                throw "REMOTE_SCOPE_MISMATCH"
            }

            $enqueue = Enqueue-Local $cmd
            if ($enqueue.status -ne "GREEN") { throw "LOCAL_ENQUEUE_FAILED" }
            $local = Wait-LocalResult ([string]$cmd.command_id)
            $ok = [string]$local.lab_command_status -eq "COMPLETED"

            $resultPayload = [ordered]@{
                device_id = $cred.device_id
                command_id = [string]$cmd.command_id
                semantic_verified = $ok
                result = [ordered]@{
                    status = [string]$local.lab_command_status
                    evidence_ref = [string]$local.lab_command_evidence
                    local_service_version = [string]$local.service_version
                    external_mutation_performed = $false
                }
            }
            $stored = Gateway-Call "POST" "/v1/agents/result" $cred.token $resultPayload
            Log "RESULT command=$($cmd.command_id) decision=$($stored.decision) semantic_verified=$ok"
            Set-LocalTransportStatus "ONLINE"
        } catch {
            Log ("LOOP_ERROR " + $_.Exception.Message)
            Set-LocalTransportStatus "ERROR"
            Start-Sleep -Seconds 15
        }
    }
} catch {
    Log ("FATAL " + $_.Exception.Message)
    Set-LocalTransportStatus "ERROR"
    exit 1
} finally {
    if ($mutex) { $mutex.ReleaseMutex() | Out-Null; $mutex.Dispose() }
}
