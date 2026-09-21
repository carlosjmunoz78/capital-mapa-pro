$ErrorActionPreference = "Stop"
$ExpectedServiceVersion = "1.4.1"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServiceCandidates = @(
    (Join-Path $ScriptDir "CerebroBrowserBridgeService.ps1"),
    (Join-Path (Resolve-Path (Join-Path $ScriptDir "..")) "windows\CerebroBrowserBridgeService.ps1")
)
$Service = $null
foreach ($Candidate in $ServiceCandidates) {
    if (Test-Path $Candidate) {
        $Service = (Resolve-Path $Candidate).Path
        break
    }
}

function Show-BridgeError([string]$Message) {
    try {
        Add-Type -AssemblyName PresentationFramework
        [System.Windows.MessageBox]::Show($Message, "CEREBRO Browser Bridge") | Out-Null
    } catch {
        Write-Host $Message
    }
}

if (-not $Service) {
    Show-BridgeError "Falta CerebroBrowserBridgeService.ps1 en el paquete. No se ha iniciado nada."
    exit 5
}

$Transport = Join-Path $ScriptDir "CerebroBrowserTransport.ps1"
$PairingFile = Join-Path $ScriptDir "PAIRING_ONCE.txt"
if (-not (Test-Path $Transport)) {
    Show-BridgeError "Falta CerebroBrowserTransport.ps1 en el paquete."
    exit 6
}

$Base = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { $HOME }
$RuntimeDir = Join-Path $Base "CEREBRO\browser-bridge"
New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
$StdoutLog = Join-Path $RuntimeDir "service.stdout.log"
$StderrLog = Join-Path $RuntimeDir "service.stderr.log"
$LauncherLog = Join-Path $RuntimeDir "launcher.log"

function Write-LauncherLog([string]$Message) {
    $line = "$(Get-Date -Format o) $Message"
    Add-Content -LiteralPath $LauncherLog -Value $line -Encoding UTF8
}

function Test-CerebroBridge([int]$Port) {
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 1
        if ($resp.StatusCode -ne 200) { return $false }
        $json = $resp.Content | ConvertFrom-Json
        return ($json.service -eq "CEREBRO Browser Bridge" -and $json.status -eq "GREEN" -and $json.service_version -eq $ExpectedServiceVersion)
    } catch {
        return $false
    }
}

function Test-PortFree([int]$Port) {
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

$RequestedPort = if ($env:CEREBRO_BRIDGE_PORT) { [int]$env:CEREBRO_BRIDGE_PORT } else { 8765 }
$Port = $RequestedPort

$ReuseExisting = $false
if (Test-CerebroBridge $Port) {
    Write-LauncherLog "Reusing existing CEREBRO Bridge on port $Port"
    $ReuseExisting = $true
}

if (-not $ReuseExisting -and -not (Test-PortFree $Port)) {
    $Found = $false
    foreach ($Candidate in 8766..8785) {
        if (Test-CerebroBridge $Candidate) {
            $Port = $Candidate
            $ReuseExisting = $true
            $Found = $true
            Write-LauncherLog "Reusing existing CEREBRO Bridge on port $Candidate"
            break
        }
        if (Test-PortFree $Candidate) {
            $Port = $Candidate
            $Found = $true
            break
        }
    }
    if (-not $Found) {
        Show-BridgeError "No hay un puerto local libre entre 8765 y 8785. CEREBRO no ha modificado otros servicios."
        exit 4
    }
}

$PowerShellExe = Join-Path $PSHOME "powershell.exe"
if (-not (Test-Path $PowerShellExe)) { $PowerShellExe = "powershell.exe" }

$TransportKeyPath = Join-Path $RuntimeDir "transport-local-key-1.4.1.txt"
if (Test-Path $TransportKeyPath) {
    $TransportKey = (Get-Content -Raw -LiteralPath $TransportKeyPath -Encoding UTF8).Trim()
}
if ([string]::IsNullOrWhiteSpace($TransportKey)) {
    $TransportKey = [Guid]::NewGuid().ToString("N")
    Set-Content -LiteralPath $TransportKeyPath -Value $TransportKey -Encoding ASCII
}

if (-not $ReuseExisting) {
    Remove-Item -LiteralPath $StdoutLog -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $StderrLog -Force -ErrorAction SilentlyContinue

    $ArgumentLine = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $Service + '" -Port ' + $Port + ' -TransportKey "' + $TransportKey + '"'
    Write-LauncherLog "Starting native PowerShell Bridge V1.4.1 on port $Port"
    $Process = Start-Process -FilePath $PowerShellExe -ArgumentList $ArgumentLine -WindowStyle Hidden -RedirectStandardOutput $StdoutLog -RedirectStandardError $StderrLog -PassThru

    $Ready = $false
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 250
        if ($Process.HasExited) { break }
        if (Test-CerebroBridge $Port) {
            $Ready = $true
            break
        }
    }

    if (-not $Ready) {
        $stderr = ""
        if (Test-Path $StderrLog) {
            $stderr = (Get-Content -Raw -LiteralPath $StderrLog -ErrorAction SilentlyContinue)
        }
        $summary = if ($stderr) { ($stderr -split "\r?\n" | Select-Object -First 4) -join " " } else { "sin detalle adicional" }
        Write-LauncherLog "FAILED: $summary"
        $nl = [Environment]::NewLine
        Show-BridgeError ("El servicio local no ha podido arrancar. Detalle: " + $summary + $nl + $nl + "Registro: " + $LauncherLog)
        exit 3
    }
} else {
    Write-LauncherLog "Existing V1.4.1 Bridge reused on port $Port"
}

$TransportStdout = Join-Path $RuntimeDir "transport.stdout.log"
$TransportStderr = Join-Path $RuntimeDir "transport.stderr.log"
$TransportArgs = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $Transport + '" -BridgePort ' + $Port + ' -TransportKey "' + $TransportKey + '" -PairingFile "' + $PairingFile + '"'
Start-Process -FilePath $PowerShellExe -ArgumentList $TransportArgs -WindowStyle Hidden -RedirectStandardOutput $TransportStdout -RedirectStandardError $TransportStderr | Out-Null
Write-LauncherLog "Cloud transport worker ensured for port $Port"

Write-LauncherLog "READY on http://127.0.0.1:$Port/"
Start-Process "http://127.0.0.1:$Port/"
