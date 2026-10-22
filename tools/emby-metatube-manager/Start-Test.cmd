@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0MediaStack.ps1" -Action Test
set "RESULT=%errorlevel%"
if not "%RESULT%"=="0" echo Action failed. Review the output above.
pause
exit /b %RESULT%
