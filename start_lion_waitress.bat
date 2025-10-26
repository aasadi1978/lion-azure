@echo off
setlocal enabledelayedexpansion

:: Prevent infinite recursion in some terminals
if not defined in_subprocess (
    cmd /k set in_subprocess=y ^& %0 %*
    exit /b
)

:: Clear screen
cls

:: Log header
echo ====================================================================== >> status.log
echo    LION: Linehaul Optimization for Network                            >> status.log
echo ====================================================================== >> status.log

:: Kill any previous python or lion instances
tasklist /fi "ImageName eq python.exe" /fo csv 2>NUL | find /I "python.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Killing existing python.exe ... >> status.log
    taskkill /IM python.exe /F >NUL
)

tasklist /fi "ImageName eq lion.exe" /fo csv 2>NUL | find /I "lion.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Killing existing lion.exe ... >> status.log
    taskkill /IM lion.exe /F >NUL
)

set FLASK_ENV=development

:: Check virtual environment existence
set VENV_DIR=.venv\Scripts
call .venv\Scripts\activate.bat
if "%ERRORLEVEL%" NEQ "0" (
    echo Failed to activate virtual environment. Please ensure it is set up correctly. >> status.log
    exit /b 1
)

call lion
if "%ERRORLEVEL%"=="0" (
    echo LION started successfully ...
)

:: Start waitress for production on windows (Use Gunicorn if Python is running linux container)
@REM echo Starting waitress...
@REM start "" http://127.0.0.1:8080/lion

@REM waitress-serve --host=127.0.0.1 --port=8000 lion.lion_app:app



endlocal
exit /b !ERRORLEVEL!
