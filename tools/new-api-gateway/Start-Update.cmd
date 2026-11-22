@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install.ps1" -Update %*
set "RESULT=%errorlevel%"
pause
exit /b %RESULT%
