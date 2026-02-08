@echo off
setlocal enabledelayedexpansion

echo.
echo ============================================
echo   ROAS Audience Recommendation Engine
echo   One-Click Setup ^& Launch
echo ============================================
echo.

:: ---- Check winget availability (needed for auto-install) ----
winget --version >nul 2>&1
if %errorlevel% neq 0 (
    set WINGET_AVAILABLE=0
    echo [INFO] winget not found - will prompt for manual install if needed
) else (
    set WINGET_AVAILABLE=1
)

:: ---- Check / Install Python ----
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python not found.
    if !WINGET_AVAILABLE! equ 1 (
        echo [..] Installing Python 3.12 via winget...
        winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
        if !errorlevel! neq 0 (
            echo [ERROR] Python install failed. Install manually from https://python.org
            pause
            exit /b 1
        )
        echo [OK] Python installed. Refreshing PATH...
        :: Refresh PATH so python/pip are available in this session
        call :RefreshPath
        python --version >nul 2>&1
        if !errorlevel! neq 0 (
            echo [WARN] Python installed but not in PATH yet.
            echo        Please close this window, open a NEW terminal, and run this script again.
            pause
            exit /b 1
        )
    ) else (
        echo [ERROR] Cannot auto-install without winget.
        echo         Install Python 3.10+ manually from https://python.org
        echo         Make sure to check "Add Python to PATH" during install.
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo [OK] %%i

:: ---- Check / Install Node.js ----
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Node.js not found.
    if !WINGET_AVAILABLE! equ 1 (
        echo [..] Installing Node.js LTS via winget...
        winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
        if !errorlevel! neq 0 (
            echo [ERROR] Node.js install failed. Install manually from https://nodejs.org
            pause
            exit /b 1
        )
        echo [OK] Node.js installed. Refreshing PATH...
        call :RefreshPath
        node --version >nul 2>&1
        if !errorlevel! neq 0 (
            echo [WARN] Node.js installed but not in PATH yet.
            echo        Please close this window, open a NEW terminal, and run this script again.
            pause
            exit /b 1
        )
    ) else (
        echo [ERROR] Cannot auto-install without winget.
        echo         Install Node.js 18+ manually from https://nodejs.org
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%i in ('node --version 2^>^&1') do echo [OK] Node.js %%i

:: ---- Check pip ----
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] pip not found. Attempting to bootstrap...
    python -m ensurepip --upgrade >nul 2>&1
    pip --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] pip is not available. Reinstall Python with pip enabled.
        pause
        exit /b 1
    )
)
echo [OK] pip available

:: ---- Check npm ----
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm not found even though Node.js is installed.
    echo         Reinstall Node.js from https://nodejs.org
    pause
    exit /b 1
)
echo [OK] npm available

echo.

:: ---- Backend .env ----
if not exist "backend\.env" (
    echo -----------------------------------------------
    echo  First-time setup: Meta App credentials needed
    echo  Get them from https://developers.facebook.com
    echo -----------------------------------------------
    echo.
    set /p META_APP_ID="  META_APP_ID: "
    set /p META_APP_SECRET="  META_APP_SECRET: "
    echo.

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
    ) > backend\.env
    echo [OK] Created backend\.env
) else (
    echo [OK] backend\.env exists
)

:: ---- Frontend .env.local ----
if not exist "frontend\.env.local" (
    echo NEXT_PUBLIC_API_URL=http://localhost:8000> frontend\.env.local
    echo [OK] Created frontend\.env.local
) else (
    echo [OK] frontend\.env.local exists
)

:: ---- Install backend dependencies ----
echo.
echo [..] Installing backend dependencies...
cd backend
pip install -r requirements.txt -q 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)
echo [OK] Backend dependencies ready
cd ..

:: ---- Install frontend dependencies ----
echo [..] Installing frontend dependencies...
cd frontend
if not exist "node_modules" (
    call npm install --silent 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
)
echo [OK] Frontend dependencies ready
cd ..

:: ---- Launch ----
echo.
echo ============================================
echo   Launching servers...
echo ============================================
echo.
echo   Backend:   http://localhost:8000
echo   Frontend:  http://localhost:3000
echo   API Docs:  http://localhost:8000/docs
echo.

:: Start backend
start "ROAS Backend" cmd /k "cd /d %~dp0backend && echo Starting backend on port 8000... && uvicorn app.main:app --reload --port 8000"

:: Give backend a head start
echo Waiting for backend to start...
timeout /t 4 /nobreak >nul

:: Start frontend
start "ROAS Frontend" cmd /k "cd /d %~dp0frontend && echo Starting frontend on port 3000... && npm run dev"

:: Wait for frontend
timeout /t 5 /nobreak >nul

:: Open browser
start http://localhost:3000

echo.
echo ============================================
echo   App is running! Browser should open now.
echo ============================================
echo.
echo   - Connect your Meta account from the homepage
echo   - Then Sync data and Generate recommendations
echo.
echo   To stop: close the "ROAS Backend" and
echo            "ROAS Frontend" terminal windows.
echo.
pause
exit /b 0

:: ---- Helper: Refresh PATH from registry ----
:RefreshPath
set "PATH="
for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%B"
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USR_PATH=%%B"
set "PATH=!SYS_PATH!;!USR_PATH!;%SystemRoot%\system32;%SystemRoot%"
goto :eof
