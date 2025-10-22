echo off
call cls

echo ------------------------------------------
echo initialising git repository ...
call git init

git config user.name "Alireza Asadi"

if "%username%"=="3626416" (
    echo ------------------------------------------
    echo setting local username and email ...
    call git config user.email "alireza.asadi@fedex.com"
) else (
    echo ------------------------------------------
    echo setting local username and email ...
    call git config user.email "a.r.asadi@gmail.com"
)

echo local repository meta data:
call git config --local user.name
call git config --local user.email
call git remote -v
echo NOTE: To set/update remote use: git remote add origin https://github.com/username/repository.git

echo ------------------------------------------
echo Here are the changes: 
call git status
echo shall I execute `git add . ` to stage all the changes (or exit batch file)?
echo ------------------------------------------

pause
call git add .
echo Staged changes:
call git status
echo Leave a comment ... 
set /p msg=leave a comment (cannot be empty!):
echo Continue with: git commit -m "%msg%" 
call git commit -m  "%msg%"

echo ------------------------------------------

if "%username%"=="3626416" (
    echo pushing to FedEx repository. Proceed? ...
    pause
    call git push origin_fdx master
) else (
    echo pushing to personal repository. Proceed? ...
    pause
    call git push origin_private master
)

