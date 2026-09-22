@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-CerebroBrowserReplayGuardV162.ps1" -Rollback
pause
