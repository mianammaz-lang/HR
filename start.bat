@echo off
title Talent Pool Management System
color 0A
echo.
echo  ================================================
echo   Talent Pool Management System
echo  ================================================
echo.

if not exist ".env" (
    echo No .env file found. Copying .env.example ...
    copy .env.example .env >nul
    echo Edit .env and set DATABASE_URL / JWT_SECRET, then re-run this script.
    pause
    exit /b 1
)

:: Kill any existing servers
taskkill /f /im python.exe >nul 2>&1

:: Setup backend
echo [1/3] Setting up backend...
cd api
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -q -r requirements.txt >nul 2>&1
cd ..

:: Setup frontend
echo [2/3] Setting up frontend...
cd frontend
if not exist "node_modules" (
    call npm install --silent
)
cd ..

:: Start backend
echo [3/3] Starting servers...
cd api
start "Backend" cmd /k "title TPMS Backend && call venv\Scripts\activate.bat && python run.py"
cd ..

timeout /t 5 /nobreak >nul

:: Start frontend
cd frontend
start "Frontend" cmd /k "title TPMS Frontend && npm run dev"
cd ..

echo.
echo  ================================================
echo   DONE! Servers are starting...
echo  ================================================
echo.
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/api/docs
echo.
echo   No admin user exists yet - see README.md "First-time setup"
echo   to create one via the protected /api/admin/seed endpoint.
echo  ================================================
echo.

timeout /t 6 /nobreak >nul
start http://localhost:3000
pause
