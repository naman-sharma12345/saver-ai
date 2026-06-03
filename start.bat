@echo off
title SaverAI Starter
echo 🚀 Starting SaverAI - Peak Perfection Edition...
echo.

:: Check if backend venv exists
if not exist "backend\venv" (
    echo ⚠️ Backend virtual environment not found. Please run setup first.
    pause
    exit /b
)

:: Start Backend in a new window
echo 📡 Launching Flask Backend...
start "SaverAI Backend" cmd /k "cd backend && venv\Scripts\activate && python run.py"

:: Wait a moment for backend to initialize
timeout /t 2 >nul

:: Start Frontend in a new window
echo 🎨 Launching Vite Frontend...
start "SaverAI Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo ✅ Servers are launching in separate windows!
echo.
echo 🔗 Frontend: http://localhost:5173
echo 🔗 Backend:  http://localhost:5000
echo.
echo Keep these windows open while using the app.
echo ===================================================
echo.
pause
