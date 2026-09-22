@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-CerebroBrowserTransportRecovery.ps1"
set EXITCODE=%ERRORLEVEL%
echo.
echo Resultado: %%LOCALAPPDATA%%\CEREBRO\browser-bridge\recovery-v1.4.3.json
pause
exit /b %EXITCODE%
