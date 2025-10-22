@echo off
:: Add the following line to prevent the app from crashing in event of error
if not defined in_subprocess (cmd /k set in_subprocess=y ^& %0 %*) & exit

call cls
                                                                                     
echo ======================================================================
echo    Opening documnetation
echo ======================================================================

set distDir="%userprofile%\TEMP_Sphinx_Dist"

start chrome %distDir%\index.html

exit

