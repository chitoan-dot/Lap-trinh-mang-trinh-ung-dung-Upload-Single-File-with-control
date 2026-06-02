@echo off
setlocal

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not added to PATH.
    echo Please install Python, then run this file again.
    pause
    exit /b 1
)

python -c "import customtkinter; from PIL import Image; import tkinterdnd2" >nul 2>&1
if errorlevel 1 (
    echo Installing required Python packages...
    python -m pip install customtkinter pillow tkinterdnd2
    if errorlevel 1 (
        echo Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo Starting server and client...
start "Upload Server" cmd /k "cd /d ""%~dp0Code"" && python main.py server"
timeout /t 1 /nobreak >nul
start "Upload Client" cmd /k "cd /d ""%~dp0Code"" && python main.py client"

echo Done. In the server window, click the Start button before uploading.
timeout /t 3 /nobreak >nul
