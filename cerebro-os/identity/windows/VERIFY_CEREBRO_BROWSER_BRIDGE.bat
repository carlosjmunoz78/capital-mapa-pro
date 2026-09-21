@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Verify-CerebroBrowserBridge.ps1"
set EXITCODE=%ERRORLEVEL%
echo.
echo Evidencia guardada en %%LOCALAPPDATA%%\CEREBRO\browser-bridge\acceptance-1.4.1.json
if not "%EXITCODE%"=="0" pause
exit /b %EXITCODE%
