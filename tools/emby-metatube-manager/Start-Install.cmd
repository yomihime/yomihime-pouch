@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Install.ps1"
set "RESULT=%errorlevel%"
if not "%RESULT%"=="0" echo Installation failed. See the actual error and log path in the installation window.
pause
exit /b %RESULT%
