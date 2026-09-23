@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-CerebroBrowserBridgeRebootAutostart.ps1"
echo.
echo CEREBRO reboot autostart installer finished.
pause
