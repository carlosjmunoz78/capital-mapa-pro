@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-CerebroBrowserBridgeRebootAutostart.ps1" -Rollback
echo.
echo CEREBRO reboot autostart rollback finished.
pause
