@echo off
rem build_windows.bat - BolgeForge native Windows entry point (cmd.exe).
rem Delegates to build_windows.ps1 so build/test logic lives in one place.
rem Usage: build_windows.bat [-Rebuild] [-Clean] [-Help]
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_windows.ps1" %*
exit /b %ERRORLEVEL%
