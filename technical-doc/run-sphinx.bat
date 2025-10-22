@echo off

:: Prevent script from crashing in case of an error
if not defined in_subprocess (
    set in_subprocess=y
    cmd /k %0 %*
    exit
)

cls

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

echo Generating documentation ...
call sphinx-build -b html %curDir% %SPHINX_PROJECT_HTML_OUTPUT_PATH%
if %errorlevel% neq 0 (
    echo Error: Sphinx build failed.
    exit /b %errorlevel%
)

@REM echo Running docs2flask.py
@REM python docs2flask.py

echo Sphinx build completed successfully. The content of dist folder has to be copied to LION\src\lion\static\technical-docs directory.

echo copying output to LION
xcopy /s /i /y "%SPHINX_PROJECT_HTML_OUTPUT_PATH%\*" "..\src\lion\static\technical-docs\"
if errorlevel 1 (
    echo Error: Failed to copy documentation to technical-docs directory.
    exit /b %errorlevel%
)

echo copying output to LION
xcopy /s /i /y "%SPHINX_PROJECT_HTML_OUTPUT_PATH%\*" "%OneDrive%\LION-UK\TechnicalDocs"
if errorlevel 1 (
    echo Error: Failed to copy documentation to TechnicalDocs directory.
    exit /b %errorlevel%
)