$ErrorActionPreference = "Stop"
$ExpectedServiceVersion = "1.3.0"

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

if (Test-CerebroBridge $Port) {
    Write-LauncherLog "Reusing existing CEREBRO Bridge on port $Port"
    Start-Process "http://127.0.0.1:$Port/"
    exit 0
}

if (-not (Test-PortFree $Port)) {
    $Found = $false
    foreach ($Candidate in 8766..8785) {
        if (Test-CerebroBridge $Candidate) {
            Write-LauncherLog "Reusing existing CEREBRO Bridge on port $Candidate"
            Start-Process "http://127.0.0.1:$Candidate/"
            exit 0
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

Remove-Item -LiteralPath $StdoutLog -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $StderrLog -Force -ErrorAction SilentlyContinue

$ArgumentLine = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $Service + '" -Port ' + $Port
Write-LauncherLog "Starting native PowerShell Bridge on port $Port"
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

Write-LauncherLog "READY on http://127.0.0.1:$Port/"
Start-Process "http://127.0.0.1:$Port/"
