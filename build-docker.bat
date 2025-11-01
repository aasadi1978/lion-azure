@echo off
cls

docker login
if %errorlevel% neq 0 (
    echo Docker login failed.
    pause
    exit /b %errorlevel%
)


echo =========================================================
echo To refresh the app version in the image, pyproject.toml must be updated first.
echo This can be done automatically when git-commit.bat is run.
echo So, make sure to run git-commit.bat before running this script to build the image.

echo ==========================================================
echo Building Docker image...

set SCM_DO_BUILD_DURING_DEPLOYMENT=false
set WEBSITES_DISABLE_ORYX=true

call az webapp config appsettings set \
  --name lion --resource-group rg-lion-app \
  --settings SCM_DO_BUILD_DURING_DEPLOYMENT=false WEBSITES_DISABLE_ORYX=true

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
