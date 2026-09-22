@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-CerebroBrowserMetadataRecovery.ps1"
set RC=%ERRORLEVEL%
echo.
echo Report: %%LOCALAPPDATA%%\CEREBRO\browser-bridge\recovery-v1.5.0.json
echo If PARTIAL: Chrome extension page chrome://extensions ^> Reload CEREBRO extension.
pause
exit /b %RC%
