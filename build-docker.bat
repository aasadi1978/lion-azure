@echo off
cls

docker login
if %errorlevel% neq 0 (
    echo Docker login failed.
    pause
    exit /b %errorlevel%
)

echo ==========================================================
echo Building Docker image...

set /p tag=Enter the Docker image tag (default is 'latest'):
if "%tag%"=="" set tag=latest

docker build -t asadi1978/lion-azure-lion-app:%tag% .
if %errorlevel% neq 0 (
    echo Docker build failed.
    pause
    exit /b %errorlevel%
)

@REM echo ==========================================================
@REM echo Running ..
@REM docker run -p 8000:8000 lion-app
@REM if %errorlevel% neq 0 (
@REM     echo Docker push failed.
@REM     pause
@REM     exit /b %errorlevel%
@REM )

echo ==========================================================
echo Pushing Docker image to Docker Hub...
docker push asadi1978/lion-azure-lion-app:%tag%
if %errorlevel% neq 0 (
    echo Docker push failed.
    pause
    exit /b %errorlevel%
)
