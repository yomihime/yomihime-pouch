@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Test-Gateway.ps1" %*
set "RESULT=%errorlevel%"
pause
exit /b %RESULT%
