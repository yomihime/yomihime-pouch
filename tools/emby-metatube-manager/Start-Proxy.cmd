@echo off
setlocal
set "MODE=%~1"
if "%MODE%"=="" set "MODE=Status"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0MediaStack.ps1" -Action "%MODE%"
set "RESULT=%errorlevel%"
if not "%RESULT%"=="0" echo Action failed. Review the output above.
pause
exit /b %RESULT%
