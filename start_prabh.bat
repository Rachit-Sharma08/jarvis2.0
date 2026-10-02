@echo off
rem Sunday (Prabh) ko chalao. Console khula rehta hai taaki crash turant dikhe.
rem Double-click karke bhi chala sakte ho.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo .venv nahi mila. README.md ke "Install" steps pehle chalao.
  echo Download: https://www.python.org/downloads/  (Python 3.12)
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -m desktop.launcher

echo.
echo Sunday band ho gaya. (exit code %errorlevel%)
echo Detail: logs\prabh.log
pause
