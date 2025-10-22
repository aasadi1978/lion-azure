echo off
call cls

echo global username and email

git config --global user.name
git config --global user.email

echo to set/update global email: git config --global user.email "a.r.asadi@gmail.com"
echo to set/update global name: git config --global user.name "Alireza Asadi"

echo ------------------------------------------

echo current repo url:
call git remote -v
echo To set/update remote use: git remote add origin https://github.com/username/repository.git

echo ------------------------------------------
echo local credentials

git config --local user.name
git config --local user.email

echo to set local email: git config --local user.email "a.r.asadi@gmail.com"
echo to set local name: git config --local user.name "Alireza Asadi"

echo ------------------------------------------
echo commit and push results

echo git commit -m "your comment comes here"
echo git push origin master

pause