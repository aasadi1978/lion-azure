:: This script installs the necessary dependencies for the LION application when installing
:: for the first time. It creates a virtual environment named "venv" if it does not exist. Then activates
:: the venv and installs the required packages.

@echo off

set LION_ENV_NAME="venv"

echo Detected python version is as follows:
call python --version
if errorlevel 1 (
    echo Python is not installed or not found in PATH.
    exit /b 1
)

if not exist %LION_ENV_NAME% (
    call python -m venv %LION_ENV_NAME%
)

echo Activating environment ...
call %LION_ENV_NAME%\Scripts\activate

call pip install -r requirements.txt
