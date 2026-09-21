@echo off
setlocal
start "" /min powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0Start-CerebroBrowserBridge.ps1"
exit /b 0
