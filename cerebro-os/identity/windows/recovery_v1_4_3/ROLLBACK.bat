@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-CerebroBrowserTransportRecovery.ps1" -Rollback
set EXITCODE=%ERRORLEVEL%
pause
exit /b %EXITCODE%
