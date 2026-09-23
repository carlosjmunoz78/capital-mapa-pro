$ErrorActionPreference="Stop"
$TaskName="CEREBRO Browser Bridge Fenix LAB v162"
$Runtime=Join-Path $env:LOCALAPPDATA "CEREBRO\browser-bridge"
$Dest=Join-Path $Runtime "autostart-v162"
$Source=Join-Path $PSScriptRoot "CerebroBridgeAutoStart.ps1"
$Record=Join-Path $Runtime "recovery-v1.6.2.json"
if(-not(Test-Path -LiteralPath $Source)) {throw "PAYLOAD_MISSING"}
if(-not(Test-Path -LiteralPath $Record)) {throw "RECOVERY_RECORD_MISSING"}
$state=Get-Content -Raw -LiteralPath $Record | ConvertFrom-Json
if($state.package_version -ne "1.6.2" -or $state.status -notin @("PARTIAL","ACCEPTED") -or
   [bool]$state.prod_enabled -or -not(Test-Path -LiteralPath ([string]$state.target))) {
  throw "INSTALLED_V162_NOT_VERIFIED"
}
if(Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
  throw "TASK_ALREADY_EXISTS_NO_OVERWRITE"
}
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
$Installed=Join-Path $Dest "CerebroBridgeAutoStart.ps1"
if(Test-Path -LiteralPath $Installed) {
  if((Get-FileHash -Algorithm SHA256 -LiteralPath $Installed).Hash -ne
     (Get-FileHash -Algorithm SHA256 -LiteralPath $Source).Hash) {throw "INSTALLED_SCRIPT_CONFLICT"}
} else {Copy-Item -LiteralPath $Source -Destination $Installed}
$Exe=Join-Path $PSHOME "powershell.exe"
if(-not(Test-Path -LiteralPath $Exe)) {$Exe="powershell.exe"}
$Action=New-ScheduledTaskAction -Execute $Exe -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "'+$Installed+'"')
$User=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$Trigger=New-ScheduledTaskTrigger -AtLogOn -User $User
$Trigger.Delay="PT30S"
$Principal=New-ScheduledTaskPrincipal -UserId $User -LogonType Interactive -RunLevel Limited
$Settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -StartWhenAvailable
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Description "Fenix LAB: Bridge 1.4.1 autostart after logon on preferred localhost 8766, no PROD" -ErrorAction Stop | Out-Null
$verified=Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
if(-not $verified) {throw "TASK_REGISTRATION_NOT_FOUND"}
[pscustomobject]@{status="REGISTERED";name=$TaskName;run_as=$User;preferred_port=8766;launch_delay_seconds=30;prod_allowed=$false;script=$Installed} | ConvertTo-Json -Depth 3
