@echo off
setlocal enabledelayedexpansion
:: Add the following line to prevent the app from crashing in event of error
if not defined in_subprocess (cmd /k set in_subprocess=y ^& %0 %*) & exit )  

call cls

echo ====================================================================== >> status.log
echo    LION: Linehaul Optimization for Network >> status.log
echo ====================================================================== >> status.log

tasklist /fi "ImageName eq python.exe" /fo csv 2>NUL | find /I "python.exe">NUL
if "%ERRORLEVEL%"=="0" taskkill /IM python.exe /F >NUL

tasklist /fi "ImageName eq lion.exe" /fo csv 2>NUL | find /I "lion.exe">NUL
if "%ERRORLEVEL%"=="0" taskkill /IM lion.exe /F >NUL

if exist !CD!\.venv\Scripts\lion.exe (
    call !CD!\.venv\Scripts\lion.exe
    if !ERRORLEVEL!==0 (
        echo Running lion ... >> status.log
    )
) else (
    echo Virtual environment not found. Please set up the virtual environment first. >> status.log
    echo You can do this by running: python -m venv .venv
    exit /b 1
)

endlocal
exit /b !ERRORLEVEL!
