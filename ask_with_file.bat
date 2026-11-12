@echo off
chcp 936 >nul
setlocal
cd /d "%~dp0"

set "FILE=%~1"
if "%FILE%"=="" set /p FILE=Path or drop file here: 

if not exist ".venv\Scripts\python.exe" (
    echo .venv not found. Run: pip install -r requirements.txt
    pause
    exit /b 1
)

.venv\Scripts\python.exe scripts\12_chat_file.py "%FILE%"

echo.
pause