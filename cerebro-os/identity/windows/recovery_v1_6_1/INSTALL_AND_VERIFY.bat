@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-CerebroBrowserReplayGuardV161.ps1"
set RC=%ERRORLEVEL%
echo Report: %LOCALAPPDATA%\CEREBRO\browser-bridge\recovery-v1.6.1.json
pause
exit /b %RC%
