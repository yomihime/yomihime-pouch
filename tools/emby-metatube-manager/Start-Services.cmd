@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0MediaStack.ps1" -Action StartServices
set "RESULT=%errorlevel%"
if not "%RESULT%"=="0" echo Service startup failed. Review the output above.
pause
exit /b %RESULT%
