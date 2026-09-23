param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1024,65535)]
    [int]$BridgePort,
    [Parameter(Mandatory = $true)]
    [string]$PairingFile
)

$ErrorActionPreference = "Stop"
$TransportVersion = "1.5.0"
$TransportPatch = "accessboot-fs-browser-v0"
$GatewayBase = "https://hnqlnvakzaywtafeiybt.supabase.co/functions/v1/cerebro-device-gateway-preprod"
$BridgeBase = "http://127.0.0.1:$BridgePort"
$Base = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { $HOME }
$RuntimeDir = Join-Path $Base "CEREBRO\browser-bridge"
$CredentialPath = Join-Path $RuntimeDir "transport-$TransportVersion.json"
$LogPath = Join-Path $RuntimeDir "transport-$TransportVersion.log"
$TransportKeyPath = Join-Path $RuntimeDir "transport-local-key-$TransportVersion.txt"

function Log([string]$Stage, [string]$Message = "", [string]$ExceptionType = "", [int]$ExitCode = -1, [string]$FailedStage = "") {
    $entry = [ordered]@{at=(Get-Date -Format o); stage=$Stage; pid=$PID}
    if ($Message) { $entry.exception_message = $Message }
    if ($ExceptionType) { $entry.exception_type = $ExceptionType }
    if ($ExitCode -ge 0) { $entry.exit_code = $ExitCode }
    if ($FailedStage) { $entry.failed_stage = $FailedStage }
    Add-Content -LiteralPath $LogPath -Value ($entry | ConvertTo-Json -Compress -Depth 3) -Encoding UTF8
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

function Invoke-CurlJson([string]$Method, [string]$Uri, [hashtable]$Headers = @{}, [object]$Body = $null, [int]$TimeoutSec = 30) {
    # PowerShell 5.1-safe transport: use .NET HttpWebRequest directly.
    # This avoids curl config/stdin/path parsing while keeping bearer values out of process arguments.
    if ($Uri.StartsWith("https://")) {
        try {
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor [System.Net.SecurityProtocolType]::Tls12
        } catch {}
    }

    $request = [System.Net.HttpWebRequest]::Create($Uri)
    $request.Method = $Method
    $request.Timeout = $TimeoutSec * 1000
    $request.ReadWriteTimeout = $TimeoutSec * 1000
    $request.UserAgent = "CEREBRO-BrowserTransport/$TransportVersion"
    $request.Accept = "application/json"

    foreach ($name in $Headers.Keys) {
        $value = [string]$Headers[$name]
        if ($value.Contains([Environment]::NewLine)) { throw "HTTP_HEADER_INVALID" }
        switch ($name.ToLowerInvariant()) {
            "content-type" { $request.ContentType = $value }
            "accept" { $request.Accept = $value }
            "user-agent" { $request.UserAgent = $value }
            default { $request.Headers[$name] = $value }
        }
    }

    if ($null -ne $Body) {
        $json = $Body | ConvertTo-Json -Depth 10 -Compress
        $bytes = (New-Object System.Text.UTF8Encoding($false)).GetBytes($json)
        $request.ContentType = "application/json"
        $request.ContentLength = $bytes.Length
        $requestStream = $request.GetRequestStream()
        try {
            $requestStream.Write($bytes, 0, $bytes.Length)
            $requestStream.Flush()
        } finally {
            $requestStream.Dispose()
        }
    }

    Log "HTTP_REQUEST_START"
    $response = $null
    try {
        $response = $request.GetResponse()
        $statusCode = [int]$response.StatusCode
        Log "HTTP_REQUEST_EXIT" "" "" $statusCode
        $responseStream = $response.GetResponseStream()
        try {
            $reader = New-Object System.IO.StreamReader($responseStream, (New-Object System.Text.UTF8Encoding($false)), $true)
            try { $text = $reader.ReadToEnd() } finally { $reader.Dispose() }
        } finally {
            if ($responseStream) { $responseStream.Dispose() }
        }
    } catch [System.Net.WebException] {
        $statusCode = -1
        if ($_.Exception.Response) {
            try { $statusCode = [int]$_.Exception.Response.StatusCode } catch {}
            try { $_.Exception.Response.Dispose() } catch {}
        }
        Log "HTTP_REQUEST_EXIT" "" "" $statusCode
        throw ("HTTP_GATEWAY_FAILED status_code=$statusCode")
    } finally {
        if ($response) { $response.Dispose() }
    }

    if ([string]::IsNullOrWhiteSpace($text)) { throw "HTTP_EMPTY_RESPONSE" }
    return ($text | ConvertFrom-Json)
}

function Gateway-Call([string]$Method, [string]$Path, [string]$Token, [object]$Body = $null) {
    $headers = @{
        Authorization = "Bearer $Token"
        "X-CEREBRO-Nonce" = New-Nonce
    }
    return Invoke-CurlJson -Method $Method -Uri ($GatewayBase + $Path) -Headers $headers -Body $Body -TimeoutSec 30
}

function Ensure-Enrolled($Bridge) {
    Log "CREDENTIAL_CHECK_START"
    $cred = Read-Credential
    if ($cred) { Log "CREDENTIAL_FOUND"; return $cred }

    Log "PAIRING_REQUIRED"
    if (-not (Test-Path $PairingFile)) { throw "PAIRING_FILE_MISSING" }
    $pairCode = (Get-Content -Raw -LiteralPath $PairingFile -Encoding UTF8).Trim()
    if ($pairCode.Length -lt 24) { throw "PAIRING_CODE_INVALID" }

    Set-LocalTransportStatus "ENROLLING"
    Log "ENROLLMENT_START"
    $token = New-Token
    $payload = [ordered]@{
        device_id = [string]$Bridge.device_id
        company_id = [string]$Bridge.company_id
        environment = [string]$Bridge.environment
        version = [string]$Bridge.version
        agent_version = "browser-transport-ps-$TransportVersion-$TransportPatch"
        pair_code = $pairCode
        token_sha256 = Sha256 $token
    }

    $response = Invoke-CurlJson -Method "POST" -Uri ($GatewayBase + "/v1/agents/enroll") -Body $payload -TimeoutSec 30
    Log "ENROLLMENT_RESPONSE_RECEIVED"
    if ($response.decision -ne "ENROLLED") { throw "ENROLLMENT_FAILED" }

    Log "ENROLLMENT_OK"
    Save-Credential $token $Bridge
    Log "CREDENTIAL_SAVED"
    Remove-Item -LiteralPath $PairingFile -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $PairingFile)) { Log "PAIRING_FILE_REMOVED" }
    return Read-Credential
}

function Validate-Scope($Bridge, $Cred) {
    if ([string]$Bridge.service -ne 'CEREBRO Browser Bridge') { throw "BRIDGE_IDENTITY_MISMATCH" }
    if ([string]$Bridge.service_version -ne $TransportVersion) { throw "BRIDGE_VERSION_MISMATCH" }
    if (-not [bool]$Bridge.paired) { throw "BRIDGE_NOT_PAIRED" }
    if ([string]$Bridge.company_id -ne "fenix" -or [string]$Bridge.environment -ne "LAB" -or [string]$Bridge.version -ne "v0") { throw "BRIDGE_SCOPE_DENIED" }
    if ($Cred) {
        if ($Cred.device_id -ne [string]$Bridge.device_id -or $Cred.company_id -ne [string]$Bridge.company_id -or $Cred.environment -ne [string]$Bridge.environment -or $Cred.version -ne [string]$Bridge.version) {
            throw "CREDENTIAL_SCOPE_MISMATCH"
        }
    }
}

function Execute-LocalCommand($Command) {
    $action = ([string]$Command.payload.action).ToUpperInvariant()

    if ($action -eq "ACCESSBOOT_CAPABILITY_SNAPSHOT") {
        $h = Local-Get "/health"
        $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        $seen = [int64]$h.extension_last_seen_at
        $extensionFresh = ($seen -gt 0 -and ($now - $seen) -ge 0 -and ($now - $seen) -le 90)
        $profiles = @()
        foreach ($p in @($h.chrome_profiles)) {
            if ($p) {
                $profiles += [ordered]@{
                    directory = [string]$p.profile_directory
                    display_name = [string]$p.display_name
                }
            }
        }
        return [ordered]@{
            direct = $true
            result = [ordered]@{
                status = "COMPLETED"
                evidence_ref = "ACCESSBOOT_CAPABILITY_SNAPSHOT"
                local_service_version = [string]$h.service_version
                company_id = [string]$h.company_id
                environment = [string]$h.environment
                version = [string]$h.version
                device_id = [string]$h.device_id
                profile_id = [string]$h.profile_id
                browser_family = [string]$h.browser_family
                browser_discovery_status = [string]$h.browser_discovery_status
                chrome_running = [bool]$h.chrome_running
                chrome_profiles = $profiles
                chrome_last_used_profile = [string]$h.chrome_last_used_profile
                extension_connected = ([string]$h.extension_status -eq "CONNECTED")
                extension_fresh = $extensionFresh
                transport_online = ([bool]$h.cloud_transport_configured -and [string]$h.cloud_transport_status -eq "ONLINE")
                paired = [bool]$h.paired
                kill_switch_enabled = [bool]$h.kill_switch_enabled
                external_mutation_performed = $false
                secret_value_included = $false
            }
        }
    }

    if ($action -eq "FS_CREATE_DIRECTORY") {
        $relative = [string]$Command.payload.relative_path
        if ([string]::IsNullOrWhiteSpace($relative) -or $relative.Length -gt 120) { throw "FS_PATH_INVALID" }
        if ($relative -match '(^[\\/]|^[A-Za-z]:|\.\.|[<>:"|?*]|[\\/]{2,})') { throw "FS_PATH_DENIED" }
        $documents = [Environment]::GetFolderPath("MyDocuments")
        if ([string]::IsNullOrWhiteSpace($documents)) { throw "DOCUMENTS_PATH_MISSING" }
        $root = [IO.Path]::GetFullPath($documents).TrimEnd('\\')
        $target = [IO.Path]::GetFullPath((Join-Path $root $relative))
        if (-not $target.StartsWith($root + "\\",[StringComparison]::OrdinalIgnoreCase)) { throw "FS_SCOPE_DENIED" }
        if (Test-Path -LiteralPath $target) {
            if (-not (Test-Path -LiteralPath $target -PathType Container)) { throw "FS_TARGET_CONFLICT" }
            $created = $false
        } else {
            New-Item -ItemType Directory -LiteralPath $target -Force | Out-Null
            $created = $true
        }
        if (-not (Test-Path -LiteralPath $target -PathType Container)) { throw "FS_READBACK_FAILED" }
        return [ordered]@{direct=$true;result=[ordered]@{
            status="COMPLETED"; evidence_ref="DIRECTORY_EXISTS_VERIFIED"; relative_path=$relative;
            created=$created; external_mutation_performed=$created; secret_value_included=$false
        }}
    }

    if ($action -notin @("OPEN_LOCAL_TEST_PAGE","READ_ONLY_PAGE_METADATA","BROWSER_OPEN_URL","OPERATOR_CLICK","OPERATOR_TYPE","OPERATOR_SELECT","OPERATOR_READ")) { throw "REMOTE_ACTION_DENIED" }
    $uri = $BridgeBase + "/cloud/enqueue?transport_key=" + [uri]::EscapeDataString($TransportKey) +
      "&command_id=" + [uri]::EscapeDataString([string]$Command.command_id) +
      "&action=" + [uri]::EscapeDataString($action)
    if ($action -eq "BROWSER_OPEN_URL") {
        $uri += "&target_url=" + [uri]::EscapeDataString([string]$Command.payload.url)
    }
    if ($action -like "OPERATOR_*") {
        $uri += "&selector=" + [uri]::EscapeDataString([string]$Command.payload.selector) +
            "&value=" + [uri]::EscapeDataString([string]$Command.payload.value)
    }
    $enqueue = Invoke-RestMethod -UseBasicParsing -Uri $uri -Method Get -TimeoutSec 5
    if ($enqueue.status -ne "GREEN") { throw "LOCAL_ENQUEUE_FAILED" }
    return [ordered]@{direct=$false}
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
$mutex = $null
$stage = "BOOT_START"
try {
    Log "BOOT_START"
    if ($BridgePort -lt 8765 -or $BridgePort -gt 8785) { throw "BRIDGE_PORT_OUT_OF_RANGE" }
    if (-not (Test-Path -LiteralPath $TransportKeyPath)) { throw "TRANSPORT_KEY_FILE_MISSING" }
    $TransportKey = (Get-Content -Raw -LiteralPath $TransportKeyPath -Encoding UTF8).Trim()
    if ($TransportKey -notmatch '^[a-fA-F0-9]{32}$') { throw "TRANSPORT_KEY_INVALID" }
    Log "ARGS_VALIDATED"
    $createdNew = $false
    $mutex = New-Object System.Threading.Mutex($true, "Local\CEREBROBrowserTransportV141", [ref]$createdNew)
    if (-not $createdNew) { Log "WORKER_EXIT" "duplicate worker"; $mutex.Dispose(); $mutex = $null; exit 0 }
    Log "MUTEX_ACQUIRED"
    $stage = "BRIDGE_CONNECT_START"
    Log $stage
    $bridge = Local-Get "/health"
    Log "BRIDGE_CONNECT_OK"
    Validate-Scope $bridge $null
    Log "SCOPE_VALIDATE_OK"
    $stage = "CREDENTIAL_CHECK_START"
    $cred = Ensure-Enrolled $bridge
    Validate-Scope $bridge $cred

    $stage = "RECONNECT_START"
    Log $stage
    $reconnect = Gateway-Call "POST" "/v1/agents/reconnect" $cred.token ([ordered]@{device_id=$cred.device_id})
    if ($reconnect.status -ne "ONLINE") { throw "RECONNECT_FAILED" }
    Log "RECONNECT_OK"
    Set-LocalTransportStatus "ONLINE"
    Log "TRANSPORT_ONLINE"

    while ($true) {
        try {
            $bridge = Local-Get "/health"
            Validate-Scope $bridge $cred
            Log "POLL_START"
            $poll = Gateway-Call "GET" ("/v1/agents/poll?device_id=" + [uri]::EscapeDataString($cred.device_id)) $cred.token
            Log "POLL_OK"
            $commands = @($poll.commands)
            if ($commands.Count -eq 0) {
                Set-LocalTransportStatus "ONLINE"
                Start-Sleep -Seconds 10
                continue
            }

            $cmd = $commands[0]
            Log "COMMAND_RECEIVED"
            if ([string]$cmd.company_id -ne $cred.company_id -or [string]$cmd.environment -ne $cred.environment -or [string]$cmd.version -ne $cred.version -or [string]$cmd.device_id -ne $cred.device_id) {
                throw "REMOTE_SCOPE_MISMATCH"
            }

            $execution = Execute-LocalCommand $cmd
            if ([bool]$execution.direct) {
                Log "LOCAL_DIRECT_EXECUTION_OK"
                $localResult = $execution.result
            } else {
                Log "LOCAL_ENQUEUE_OK"
                $local = Wait-LocalResult ([string]$cmd.command_id)
                Log "LOCAL_RESULT_OK"
                $localResult = [ordered]@{
                    status = [string]$local.lab_command_status
                    evidence_ref = [string]$local.lab_command_evidence
                    local_service_version = [string]$local.service_version
                    external_mutation_performed = $false
                    secret_value_included = $false
                    observed_url = [string]$local.lab_command_observed_url
                    observed_title = [string]$local.lab_command_observed_title
                    page_load_complete = [bool]$local.lab_command_page_load_complete
                    page_content_included = $false
                    observed_value = [string]$local.lab_command_observed_value
                }
            }
            $ok = [string]$localResult.status -eq "COMPLETED"
            if ([string]$cmd.payload.action -eq "FS_CREATE_DIRECTORY") {
                $ok = $ok -and [string]$localResult.evidence_ref -ceq "DIRECTORY_EXISTS_VERIFIED" -and
                    [string]$localResult.relative_path -ceq [string]$cmd.payload.relative_path
            }
            if ([string]$cmd.payload.action -eq "BROWSER_OPEN_URL") {
                $ok = $ok -and [string]$localResult.evidence_ref -ceq "BROWSER_URL_OPENED_VERIFIED" -and
                    [string]$localResult.observed_url -ceq [string]$cmd.payload.url -and [bool]$localResult.page_load_complete
            }

            if ([string]$cmd.payload.action -eq "READ_ONLY_PAGE_METADATA") {
                $ok = $ok -and
                    [string]$localResult.evidence_ref -ceq "EXAMPLE_DOMAIN_METADATA_VERIFIED" -and
                    [string]$localResult.observed_url -ceq "https://example.com/" -and
                    [string]$localResult.observed_title -ceq "Example Domain" -and
                    [bool]$localResult.page_load_complete
            }

            if ([string]$cmd.payload.action -like "OPERATOR_*") {
                $operatorAction = [string]$cmd.payload.action
                $observed = [string]$localResult.observed_value
                $expected = [string]$cmd.payload.value
                $ok = $ok -and [string]$localResult.evidence_ref -ceq "LAB_OPERATOR_FIXTURE_VERIFIED" -and
                    (($operatorAction -eq "OPERATOR_CLICK" -and $observed -ceq "CLICKED") -or
                     ($operatorAction -eq "OPERATOR_TYPE" -and $observed -ceq $expected -and $observed.Length -gt 0 -and $observed.Length -le 64) -or
                     ($operatorAction -eq "OPERATOR_SELECT" -and $observed -ceq $expected -and $observed -cin @("alpha","beta")) -or
                     ($operatorAction -eq "OPERATOR_READ" -and $observed -cin @("READY","CLICKED")))
            }
            $resultPayload = [ordered]@{
                device_id = $cred.device_id
                command_id = [string]$cmd.command_id
                semantic_verified = $ok
                result = $localResult
            }
            $stored = Gateway-Call "POST" "/v1/agents/result" $cred.token $resultPayload
            Log "REMOTE_RESULT_STORED"
            Set-LocalTransportStatus "ONLINE"
        } catch {
            Log "LOOP_ERROR" $_.Exception.Message $_.Exception.GetType().FullName
            Set-LocalTransportStatus "ERROR"
            Start-Sleep -Seconds 15
        }
    }
} catch {
    Log "FATAL" $_.Exception.Message $_.Exception.GetType().FullName -1 $stage
    Set-LocalTransportStatus "ERROR"
    exit 1
} finally {
    Log "WORKER_EXIT"
    if ($mutex -and $createdNew) { $mutex.ReleaseMutex() | Out-Null; $mutex.Dispose() }
}
