@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title VocalPrint AI Launcher

echo ============================================
echo    VocalPrint AI - Application Launcher
echo ============================================
echo.

:: --- [0/4] Cleanup zombie processes ------------------------------------------
echo [0/4] Cleaning up existing processes on ports 8500 and 8081...

:: kill by port
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8500 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8081 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1

:: kill by name (aggressive)
taskkill /F /IM node.exe /FI "WINDOWTITLE eq VocalPrint Frontend*" >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq VocalPrint Backend*" >nul 2>&1

:: --- [1/4] Checking dependencies -------------------------------------------
echo [1/4] Checking dependencies...

:: Frontend check
if not exist "node_modules" (
    echo [!] node_modules not found. Running npm install...
    npm install
)

:: Backend check
cd /d "%~dp0backend"
if not exist "venv\Scripts\activate.bat" (
    echo [!] Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
python check_ready.py
if errorlevel 1 (
    echo [!] Reinstalling backend requirements...
    pip install -r requirements.txt
    python check_ready.py
)

echo.
echo [2/4] Starting Backend (FastAPI)...
start "VocalPrint Backend" /min cmd /c "chcp 65001 >nul && call venv\Scripts\activate.bat && python main.py"

:: --- [3/4] Wait for backend ------------------------------------------------
echo [3/4] Waiting for backend (Librosa warmup)...
set /a attempts=0
:WAIT_BACKEND
set /a attempts+=1
if %attempts% GTR 60 (
    echo [!] Backend timeout.
    pause
    goto START_FRONTEND
)
powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri 'http://127.0.0.1:8500/' -UseBasicParsing).StatusCode -eq 200 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto WAIT_BACKEND
)
echo [OK] Backend ready!

:: --- [4/4] Starting Frontend -----------------------------------------------
:START_FRONTEND
echo.
echo [4/4] Starting Frontend (Vite)...
cd /d "%~dp0"
start "VocalPrint Frontend" /min cmd /c "chcp 65001 >nul && npm run dev"

echo Waiting for Frontend (7 sec)...
timeout /t 7 /nobreak >nul

echo Opening browser...
start "" "http://127.0.0.1:8081"

echo.
echo ============================================
echo    VocalPrint AI is running!
echo    URL: http://127.0.0.1:8081
echo ============================================
pause
exit
