@echo off
setlocal
set "CEREBRO_ZEUS_PS=%TEMP%\cerebro_zeus_prueba_%RANDOM%%RANDOM%.ps1"
> "%CEREBRO_ZEUS_PS%" echo $ErrorActionPreference = 'Stop'
>> "%CEREBRO_ZEUS_PS%" echo try {
>> "%CEREBRO_ZEUS_PS%" echo   $docs = [Environment]::GetFolderPath('MyDocuments')
>> "%CEREBRO_ZEUS_PS%" echo   if ([string]::IsNullOrWhiteSpace($docs)) { throw 'DOCUMENTS_PATH_NOT_FOUND' }
>> "%CEREBRO_ZEUS_PS%" echo   $folder = Join-Path $docs 'Cerebro Zeus'
>> "%CEREBRO_ZEUS_PS%" echo   $existed = Test-Path -LiteralPath $folder -PathType Container
>> "%CEREBRO_ZEUS_PS%" echo   [void](New-Item -ItemType Directory -Path $folder -Force)
>> "%CEREBRO_ZEUS_PS%" echo   $chrome = $null
>> "%CEREBRO_ZEUS_PS%" echo   foreach ($p in @((Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'), (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe'), (Join-Path $env:LOCALAPPDATA 'Google\Chrome\Application\chrome.exe'))) { if ($p -and (Test-Path -LiteralPath $p -PathType Leaf)) { $chrome = $p; break } }
>> "%CEREBRO_ZEUS_PS%" echo   if (-not $chrome) { throw 'CHROME_NOT_FOUND' }
>> "%CEREBRO_ZEUS_PS%" echo   $p = Start-Process -FilePath $chrome -ArgumentList @('--profile-directory=Default', 'https://www.youtube.com/') -PassThru
>> "%CEREBRO_ZEUS_PS%" echo   $out = @('CEREBRO_ZEUS_TEST', ('timestamp=' + (Get-Date -Format o)), ('folder=' + $folder), ('folder_exists=' + (Test-Path -LiteralPath $folder -PathType Container)), ('folder_preexisted=' + $existed), ('browser_process_started=' + [bool]$p), ('browser=Chrome Default'), 'url=https://www.youtube.com/', 'NOTE: browser page load and actual screen appearance require visual confirmation')
>> "%CEREBRO_ZEUS_PS%" echo   $out ^| Set-Content -LiteralPath (Join-Path $folder 'CEREBRO_ZEUS_RESULT.txt') -Encoding UTF8
>> "%CEREBRO_ZEUS_PS%" echo   $out ^| ForEach-Object { Write-Host $_ }
>> "%CEREBRO_ZEUS_PS%" echo } catch { Write-Host ('FAILED: ' + $_.Exception.Message); exit 1 }
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%CEREBRO_ZEUS_PS%"
set "CEREBRO_ZEUS_EXIT=%ERRORLEVEL%"
del /q "%CEREBRO_ZEUS_PS%" >nul 2>&1
echo.
if "%CEREBRO_ZEUS_EXIT%"=="0" (echo CEREBRO ZEUS: SCRIPT FINISHED. Check that YouTube opened in Chrome.) else (echo CEREBRO ZEUS: SCRIPT FAILED. Send me the FAILED line.)
echo.
pause
exit /b %CEREBRO_ZEUS_EXIT%
