$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$ServiceCandidates = @(
    (Join-Path $ScriptDir "browser_bridge_local_service.py"),
    (Join-Path (Resolve-Path (Join-Path $ScriptDir "..")) "browser_bridge_local_service.py")
)
$Service = $null
foreach ($Candidate in $ServiceCandidates) {
    if (Test-Path $Candidate) {
        $Service = (Resolve-Path $Candidate).Path
        break
    }
}
if (-not $Service) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
      "No se encuentra browser_bridge_local_service.py junto al launcher ni en la carpeta esperada.",
      "CEREBRO Browser Bridge"
    ) | Out-Null
    exit 5
}
$BridgeRoot = Split-Path -Parent $Service

function Find-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @("py","-3") }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @("python") }
    return $null
}

function Test-CerebroBridge {
    param([int]$Port)
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 1
        if ($resp.StatusCode -ne 200) { return $false }
        $json = $resp.Content | ConvertFrom-Json
        return ($json.service -eq "CEREBRO Browser Bridge" -and $json.status -eq "GREEN")
    } catch {
        return $false
    }
}

function Test-PortFree {
    param([int]$Port)
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback,$Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

$Python = Find-Python
if (-not $Python) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
      "No se ha encontrado Python 3 en este PC. CEREBRO Browser Bridge no se ha iniciado.",
      "CEREBRO Browser Bridge"
    ) | Out-Null
    exit 2
}

$RequestedPort = if ($env:CEREBRO_BRIDGE_PORT) { [int]$env:CEREBRO_BRIDGE_PORT } else { 8765 }
$Port = $RequestedPort

if (Test-CerebroBridge -Port $Port) {
    Start-Process "http://127.0.0.1:$Port/"
    exit 0
}

if (-not (Test-PortFree -Port $Port)) {
    $Found = $false
    foreach ($Candidate in 8766..8785) {
        if (Test-CerebroBridge -Port $Candidate) {
            Start-Process "http://127.0.0.1:$Candidate/"
            exit 0
        }
        if (Test-PortFree -Port $Candidate) {
            $Port = $Candidate
            $Found = $true
            break
        }
    }
    if (-not $Found) {
        Add-Type -AssemblyName PresentationFramework
        [System.Windows.MessageBox]::Show(
          "No hay un puerto local libre entre 8765 y 8785. CEREBRO no ha modificado ningun otro servicio.",
          "CEREBRO Browser Bridge"
        ) | Out-Null
        exit 4
    }
}

$env:CEREBRO_BRIDGE_PORT = [string]$Port
$Args = @()
if ($Python.Count -gt 1) { $Args += $Python[1] }
$Args += @($Service)

$Exe = $Python[0]
$WorkDir = Split-Path -Parent $BridgeRoot
$Process = Start-Process -FilePath $Exe -ArgumentList $Args -WorkingDirectory $WorkDir -WindowStyle Hidden -PassThru

$Ready = $false
for ($i=0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 200
    if ($Process.HasExited) { break }
    if (Test-CerebroBridge -Port $Port) { $Ready = $true; break }
}

if (-not $Ready) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
      "El servicio local no ha podido arrancar. No se ha tocado PROD ni se han enviado credenciales.",
      "CEREBRO Browser Bridge"
    ) | Out-Null
    exit 3
}

Start-Process "http://127.0.0.1:$Port/"
