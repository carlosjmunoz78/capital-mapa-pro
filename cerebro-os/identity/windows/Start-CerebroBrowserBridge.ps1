$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Resolve-Path (Join-Path $ScriptDir "..")
$Service = Join-Path $BridgeRoot "browser_bridge_local_service.py"
$Port = if ($env:CEREBRO_BRIDGE_PORT) { $env:CEREBRO_BRIDGE_PORT } else { "8765" }

function Find-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @("py","-3") }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @("python") }
    return $null
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

$Url = "http://127.0.0.1:$Port/"
try {
    $existing = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 1
    if ($existing.StatusCode -eq 200) {
        Start-Process $Url
        exit 0
    }
} catch {}

$Args = @()
if ($Python.Count -gt 1) { $Args += $Python[1] }
$Args += @($Service)

$Exe = $Python[0]
$WorkDir = Split-Path -Parent $BridgeRoot
$Process = Start-Process -FilePath $Exe -ArgumentList $Args -WorkingDirectory $WorkDir -WindowStyle Hidden -PassThru

$Ready = $false
for ($i=0; $i -lt 25; $i++) {
    Start-Sleep -Milliseconds 200
    if ($Process.HasExited) { break }
    try {
        $health = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 1
        if ($health.StatusCode -eq 200) { $Ready = $true; break }
    } catch {}
}

if (-not $Ready) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
      "El servicio local no ha podido arrancar. No se ha tocado PROD ni se han enviado credenciales.",
      "CEREBRO Browser Bridge"
    ) | Out-Null
    exit 3
}

Start-Process $Url
