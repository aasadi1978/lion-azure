@echo off
if not defined in_subprocess (cmd /k set in_subprocess=y ^& %0 %*) & exit )  

setlocal enabledelayedexpansion

call cls

rmdir /s /q !CD!\dist

set "LION_ENV_NAME=.venv"
set "python_exe=!LION_ENV_NAME!\Scripts\python.exe"

call !LION_ENV_NAME!\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo Failed to activate virtual environment. Exiting ...
    goto exiting
)

call !python_exe! -m pip install --upgrade pip setuptools wheel
if !ERRORLEVEL! neq 0 echo Failed to upgrade pip, setuptools, or wheel.

if exist !CD!\dist (
    rmdir /s /q !CD!\dist
    if !ERRORLEVEL! neq 0 (
        echo Failed to remove existing dist directory.
    )
)

echo building the distributable packages, *.tar.gz and *.whl files ... please wait ...
@REM --wheel → builds only .whl
@REM --sdist → builds only .tar.gz
call !python_exe! -m build --wheel
if !ERRORLEVEL! neq 0 (
    echo Build process failed. Please check the output for details.
    echo Build process failed. Please check the output for details. > build.log
)


if not exist !CD!\dist\* (
    echo No files found in dist directory. Exiting ...
    goto exiting
)

rmdir /s /q !CD!\build

if exist !CD!\build.log (
    del /q !CD!\build.log
)


endlocal
