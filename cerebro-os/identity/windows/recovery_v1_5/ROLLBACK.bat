@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-CerebroBrowserMetadataRecovery.ps1" -Rollback
set RC=%ERRORLEVEL%
pause
exit /b %RC%
