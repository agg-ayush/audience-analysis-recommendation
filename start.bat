@echo off
echo.
echo ============================================
echo   Starting ROAS Recommendation Engine
echo ============================================
echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo.
echo   Press Ctrl+C in either window to stop.
echo ============================================
echo.

:: Start backend in a new window
start "ROAS Backend" cmd /k "cd /d %~dp0backend && uvicorn app.main:app --reload --port 8000"

:: Wait a moment for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend in a new window
start "ROAS Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

:: Wait and open browser
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo Both servers started. Opening browser...
echo Close the terminal windows to stop.
