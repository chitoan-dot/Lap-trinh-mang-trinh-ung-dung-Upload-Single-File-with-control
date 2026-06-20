@echo off
setlocal EnableExtensions

title UPLOWER Project Launcher
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH.
    echo Install Python 3.10 or newer, then run this file again.
    pause
    exit /b 1
)

if not exist "%~dp0Code\main.py" (
    echo [ERROR] Cannot find Code\main.py.
    echo Project directory: %~dp0
    pause
    exit /b 1
)

if not exist "%~dp0requirements.txt" (
    echo [ERROR] Cannot find requirements.txt.
    pause
    exit /b 1
)

python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    python -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo [ERROR] Failed to install required packages.
        pause
        exit /b 1
    )
)

echo Starting UPLOWER Server...
start "UPLOWER Server" /D "%~dp0Code" python main.py server

timeout /t 2 /nobreak >nul

echo Starting UPLOWER Client...
start "UPLOWER Client" /D "%~dp0Code" python main.py client

echo Server and Client were started successfully.
echo Click Start in the Server window before uploading a file.
timeout /t 3 /nobreak >nul

endlocal
exit /b 0