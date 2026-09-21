@echo off
setlocal
set "EXTDIR=%~dp0chrome_extension_v1_4_1"
if not exist "%EXTDIR%\manifest.json" (
  echo No se encuentra la extension CEREBRO V1.4.1 en:
  echo %EXTDIR%
  pause
  exit /b 2
)

start "" explorer.exe "%EXTDIR%"

set "CHROME="
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"

if defined CHROME (
  start "" "%CHROME%" "chrome://extensions/"
) else (
  start "" "chrome://extensions/"
)

echo.
echo CEREBRO Browser Bridge V1.4.1
echo 1. Activa "Modo de desarrollador" en chrome://extensions
echo 2. Pulsa "Cargar descomprimida"
echo 3. Selecciona la carpeta abierta chrome_extension_v1_4_1
echo.
echo No introduzcas contrasenas ni tokens.
pause
endlocal
