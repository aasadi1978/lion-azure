@echo off
cls

docker-compose up --build
if %errorlevel% neq 0 (
    echo Docker build failed.
    pause
    exit /b %errorlevel%
)