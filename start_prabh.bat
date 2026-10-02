@echo off
rem Sunday ko chalao. Console khula rehta hai taaki crash turant dikhe.
rem Double-click karke bhi chala sakte ho.
rem NOTE: is file me kabhi raw bracket mat likho. cmd ka if-block beech me
rem toot jaata hai aur python chala hi nahi hota - Phase 5 ka asli bug.
rem Is liye yahan goto label use hua hai, bracket block nahi.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" goto novenv

".venv\Scripts\python.exe" -m desktop.launcher
set "RC=%errorlevel%"

echo.
echo Sunday band ho gaya. Exit code %RC%
echo Detail   : logs\prabh.log
echo Crash    : logs\desktop.out
pause
exit /b %RC%

:novenv
echo .venv nahi mila. README.md ke Install steps pehle chalao.
echo Download: https://www.python.org/downloads/ -- Python 3.12
pause
exit /b 1
