setlocal enabledelayedexpansion
@echo off

echo Do not forget to update pyproject.toml version if applicable before committing.
echo Press any key to continue ...

git init
git status

set /p commit_message=Enter commit message:
if "%commit_message%" neq "" (
    git add .
    git commit -m "%commit_message%"
    if errorlevel 1 (
        echo Commit failed. Please check the error messages above.
        exit /b 1
    ) else (
        echo Commit successful.
    )
) else (
    echo %commit_message%
    echo Commit message cannot be empty. Aborting commit.
    exit /b 1
)

:tagging
echo Managing tags ...
echo Top 5 tags:
echo Make sure the version in pyproject.toml is updated if applicable.
echo To delete a tag, use git tag -d tagname
echo ------------------------------------------------------------

set /p tag=Enter tag name (or press Enter to skip tagging -  will delete the tag if exists):
if "%tag%" neq "" (

    git tag -d "%tag%" 2>nul
    git push --delete origin "%tag%" 2>nul
    git push --delete origin_private "%tag%" 2>nul
    if errorlevel 1 (
        echo No existing tag named "%tag%" to delete.
    ) else (
        echo Deleted existing tag named "%tag%".
    )

    git tag "%tag%"
    if errorlevel 1 (
        tag=""
        echo Tagging failed. Please check the error messages above.
        goto tagging
    ) else (
        echo Tagging successful.
        goto committing_done
    )
) else (
    echo Skipping tagging.
)

:committing_done
echo ------------------------------------------------------------
echo Recent commit history:
@REM git log: Shows the commit history.
@REM --oneline: Each commit is shown as a single line (short hash + message).
@REM --decorate: Shows branch and tag names next to commits.
@REM --graph: Adds an ASCII graph showing branch and merge structure.
@REM --all: Includes all branches, not just the current one.
git log --oneline --decorate --graph --all -10
echo ------------------------------------------------------------

echo You can now push your changes using 'git push' command.
echo The following remotes are available:
git remote -vs

set /p push_confirm=Do you want to push now? (y/n):
if /i "%push_confirm%"=="y" (
    
    echo Pushing to remote repository origin
    git push origin master
    if errorlevel 1 (
        echo Push failed. Please check the error messages above.
        exit /b 1
    ) else (
        echo Push successful.
    )

    echo Pushing to remote repository - origin_private
    git push origin_private master
    if errorlevel 1 (
        echo Push failed. Please check the error messages above.
        exit /b 1
    ) else (
        echo Push successful.
    )

) else (
    echo Skipping push. You can push later using 'git push' command.
)

echo Pushing tags to remote repositories origin and origin_private
@REM git push origin --tags
if "%tag%"=="" (
    echo No tag to push.
) else (
    echo Pushing tag %tag% to origin
    git push origin tag %tag%
    if errorlevel 1 (
        echo Push tags to origin failed. Please check the error messages above.
    ) else (
        echo Push tags to origin successful.
    )

    @REM echo Pushing tag %tag% to origin and origin_private
    @REM git push origin_private tag %tag%
    @REM if errorlevel 1 (
    @REM     echo Push tags to origin_private failed. Please check the error messages above.
    @REM ) else (
    @REM     echo Push tags to origin_private successful.
    @REM )
)

set /p build_pkg=Do you want to build a wheel file? (y/n):

if /i "%build_pkg%"=="y" (
    echo Building the package...
    call build-distributable-package.bat
    if errorlevel 1 (
        echo Build and push process failed. Please check the error messages above.
        exit /b 1
    ) else (
        echo Build and push process completed successfully.
    )
) else (
    echo Skipping package build and push.
)

endlocal