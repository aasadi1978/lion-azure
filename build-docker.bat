@echo off
cls

@REM docker-compose up --build
@REM if %errorlevel% neq 0 (
@REM     echo Docker build failed.
@REM     pause
@REM     exit /b %errorlevel%
@REM )

@REM -u asadi1978 -p %DOCKER_HUB_PASSWORD%
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

echo ==========================================================
echo Pushing Docker image to Docker Hub...
docker push asadi1978/lion-azure-lion-app:%tag%
if %errorlevel% neq 0 (
    echo Docker push failed.
    pause
    exit /b %errorlevel%
)