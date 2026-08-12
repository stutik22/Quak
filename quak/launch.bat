@echo off
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    🍳 QWAK Recipe Recommender                ║
echo ║                     Windows Launcher                         ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo Starting QWAK Recipe Recommender...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Start backend in a new window
echo 🚀 Starting backend server...
start "QWAK Backend" cmd /k "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
echo 🎨 Starting frontend app...
start "QWAK Frontend" cmd /k "cd frontend && python -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0"

REM Wait for services to initialize
echo ⏳ Waiting for services to start...
timeout /t 5 /nobreak >nul

echo.
echo ═══════════════════════════════════════════════════════════════
echo 🎉 QWAK Recipe Recommender is starting!
echo ═══════════════════════════════════════════════════════════════
echo 🔗 Frontend: http://localhost:8501
echo 🔗 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo ═══════════════════════════════════════════════════════════════
echo.
echo 💡 Two new windows have opened for backend and frontend
echo 💡 Close those windows to stop the services
echo.

REM Try to open the frontend in default browser
echo 🌐 Opening frontend in browser...
start http://localhost:8501

echo ✅ Launch complete!
echo.
pause