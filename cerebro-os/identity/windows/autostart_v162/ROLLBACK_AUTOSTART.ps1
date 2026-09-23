$ErrorActionPreference="Stop"
$TaskName="CEREBRO Browser Bridge Fenix LAB v162"
$Runtime=Join-Path $env:LOCALAPPDATA "CEREBRO\browser-bridge"
$Installed=Join-Path $Runtime "autostart-v162\CerebroBridgeAutoStart.ps1"
$task=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if(-not $task) {"NOT_REGISTERED";exit 0}
$match=@($task.Actions | Where-Object {$_.Arguments -like '*CerebroBridgeAutoStart.ps1*' -and $_.Arguments -like '*autostart-v162*'})
if($match.Count -ne 1) {throw "TASK_OWNERSHIP_MISMATCH_NO_DELETE"}
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
# Preserve script, logs and current running Bridge; rollback removes only our scheduled task.
[pscustomobject]@{status="AUTOSTART_REMOVED";running_bridge_untouched=$true;credentials_untouched=$true;files_preserved=$true;script=$Installed} | ConvertTo-Json
