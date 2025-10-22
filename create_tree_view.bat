@echo off
setlocal enabledelayedexpansion
:: Add the following line to prevent the app from crashing in event of error
if not defined in_subprocess (cmd /k set in_subprocess=y ^& %0 %*) & exit )  

@REM This scripts start lion assuming that reginal settings are already set. We use this batch file
@REM to reboot existing lion.

call cls
set currPath=%~dp0

echo ======================================================================
echo    LION: Linehaul Optimization for Network
echo ======================================================================


echo Activating virtual environment ...
call .venv\Scripts\activate.bat

echo Executing proj_tree_view.py
python proj_tree_view.py
if %ERRORLEVEL% neq 0 (
    echo Executing proj_tree_view.py failed ...
    echo Error code: %ERRORLEVEL%
    exit /b 1
)

echo proj_tree_view.py not found!
endlocal

:exiting
exit /b