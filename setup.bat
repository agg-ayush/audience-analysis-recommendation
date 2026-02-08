@echo off
setlocal enabledelayedexpansion

echo.
echo ============================================
echo   ROAS Audience Recommendation Engine Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)
echo [OK] Python found

:: Check Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install Node.js 18+ from nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found

:: Check npm
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm not found.
    pause
    exit /b 1
)
echo [OK] npm found
echo.

:: ---- Backend setup ----
echo --- Setting up backend ---
cd backend

if not exist ".env" (
    echo.
    echo You need Meta App credentials to connect ad accounts.
    echo Get them from https://developers.facebook.com/apps
    echo.
    set /p META_APP_ID="Enter META_APP_ID (or press Enter to skip): "
    set /p META_APP_SECRET="Enter META_APP_SECRET (or press Enter to skip): "

    (
        echo APP_ENV=development
        echo SECRET_KEY=roas-dev-%RANDOM%%RANDOM%
        echo FRONTEND_URL=http://localhost:3000
        echo BACKEND_URL=http://localhost:8000
        echo DATABASE_URL=sqlite:///./roas.db
        echo META_APP_ID=!META_APP_ID!
        echo META_APP_SECRET=!META_APP_SECRET!
        echo META_REDIRECT_URI=http://localhost:8000/api/auth/meta/callback
        echo ANTHROPIC_API_KEY=
    ) > .env
    echo [OK] Created backend\.env
) else (
    echo [OK] backend\.env already exists
)

echo Installing Python dependencies...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed
    pause
    exit /b 1
)
echo [OK] Backend dependencies installed
cd ..

:: ---- Frontend setup ----
echo.
echo --- Setting up frontend ---
cd frontend

if not exist ".env.local" (
    echo NEXT_PUBLIC_API_URL=http://localhost:8000> .env.local
    echo [OK] Created frontend\.env.local
) else (
    echo [OK] frontend\.env.local already exists
)

echo Installing Node dependencies...
call npm install --silent
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed
    pause
    exit /b 1
)
echo [OK] Frontend dependencies installed
cd ..

echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo   To start the app, run:  start.bat
echo   Or start manually:
echo     Terminal 1:  cd backend ^& uvicorn app.main:app --reload --port 8000
echo     Terminal 2:  cd frontend ^& npm run dev
echo.
pause
