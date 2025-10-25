@echo off
if not defined in_subprocess (cmd /k set in_subprocess=y ^& %0 %*) & exit )  

setlocal enabledelayedexpansion

call cls

cd /d %~dp0
set assets_dir=!CD!\Onboarding\assets

echo ======================================================================
echo    LION: Building distributable application
echo ======================================================================

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

echo Build process completed. Moving to onboarding assets directory ...

if not exist !assets_dir! (
    mkdir !assets_dir!
    if !ERRORLEVEL! neq 0 (
        echo Failed to create assets directory in onboarding.
        goto exiting
    )
)

echo Copying distributable packages to onboarding assets directory ...
if not exist !CD!\dist\* (
    echo No files found in dist directory. Exiting ...
    goto exiting
)

move /Y !CD!\dist\* !assets_dir!
if !ERRORLEVEL!==0 (
    rmdir /s /q !CD!\dist
    if !ERRORLEVEL! neq 0 (
        echo Failed to remove dist directory after moving files.
    )
)

set /p push_pkg=Do you want to copy the wheel file to OneDrive onboarding directory? (y/n):
if /i "%push_pkg%"=="y" (

    echo Copying the wheel file to OneDrive onboarding directory ...

    set "dest_dir=%OneDrive%\LION-UK\_onboarding_"

    echo Copying .whl files from dist to destination...
    robocopy "!assets_dir!" "!dest_dir!" *.whl /XO /R:2 /W:2 /NFL /NDL /NJH /NJS > nul
    if !ERRORLEVEL! GEQ 8 (
        echo Failed to copy .whl files to OneDrive onboarding directory.
        goto exiting
    )

    :: Rename any copied .whl file to lion-latest-py3-none-any.whl
    for %%f in ("!assets_dir!\*.whl") do (
        echo Renaming %%~nxf to lion-latest-py3-none-any.whl
        ren "!dest_dir!\%%~nxf" "lion-latest-py3-none-any.whl"
    )

    if exist "!dest_dir!\lion-latest-py3-none-any.whl" (
        echo Successfully copied and renamed the wheel file to OneDrive onboarding directory.
    ) else (
        echo Failed to find the renamed wheel file in OneDrive onboarding directory.
    )
)

rmdir /s /q !CD!\build
del /q !CD!\build.log

endlocal
