@echo off

:: Prevent script from crashing in case of an error
if not defined in_subprocess (
    set in_subprocess=y
    cmd /k %0 %*
    exit
)

cls
@REM call config.bat

echo ======================================================================
echo    Building Sphinx-documentation
echo ======================================================================

if exist .venv (
    echo activating .venv ...
    call .venv\Scripts\activate.bat
) else (
    echo creating .venv ...
    call python -m .venv .venv
    call .venv\Scripts\activate.bat
    call .venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
    call .venv\Scripts\python.exe -m pip install -r requirements.txt
)

set curDir=%cd%
set "SPHINX_PROJECT_HTML_OUTPUT_PATH=%curDir%\dist"

if exist "%SPHINX_PROJECT_HTML_OUTPUT_PATH%" (
    rmdir /s /q "%SPHINX_PROJECT_HTML_OUTPUT_PATH%"
)
mkdir "%SPHINX_PROJECT_HTML_OUTPUT_PATH%"

echo installing dependencies ...
call pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Failed to install requirements.
    exit /b %errorlevel%
)

call sphinx-build -b html %curDir% %SPHINX_PROJECT_HTML_OUTPUT_PATH%
if %errorlevel% neq 0 (
    echo Error: Sphinx build failed.
    exit /b %errorlevel%
)

echo Sphinx build completed successfully. The content of dist folder has to be copied to LION\src\lion\static\user-manual directory.
@REM echo Running docs2flask.py
@REM python docs2flask.py

echo copying output to LION
xcopy /s /i /y "%SPHINX_PROJECT_HTML_OUTPUT_PATH%\*" "..\src\lion\static\user-manual\"
if errorlevel 1 (
    echo Error: Failed to copy documentation to LION directory.
    exit /b %errorlevel%
)

echo copying output to LION
xcopy /s /i /y "%SPHINX_PROJECT_HTML_OUTPUT_PATH%\*" "%OneDrive%\LION-UK\UserManual"
if errorlevel 1 (
    echo Error: Failed to copy documentation to LION directory.
    exit /b %errorlevel%
)


:: start chrome "%CD%\%SPHINX_PROJECT_HTML_OUTPUT_PATH%\index.html"
