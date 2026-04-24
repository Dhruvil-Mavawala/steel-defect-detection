@echo off
setlocal enabledelayedexpansion

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║   Steel Defect Pro — Clean Environment Setup        ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: ── Step 1: Remove old venv if exists ────────────────────────────────────────
if exist "venv" (
    echo [1/7] Removing old venv...
    rmdir /s /q venv
    echo       Done.
) else (
    echo [1/7] No existing venv found. Skipping.
)

:: ── Step 2: Create fresh venv with Python 3.10 ───────────────────────────────
echo.
echo [2/7] Creating fresh virtual environment...
py -3.10 -m venv venv
if errorlevel 1 (
    echo ERROR: Python 3.10 not found. Install from https://www.python.org/downloads/release/python-31011/
    pause & exit /b 1
)
echo       Done.

:: ── Step 3: Activate venv ────────────────────────────────────────────────────
echo.
echo [3/7] Activating venv...
call venv\Scripts\activate.bat
echo       Done.

:: ── Step 4: Upgrade pip toolchain ────────────────────────────────────────────
echo.
echo [4/7] Upgrading pip, setuptools, wheel...
python -m pip install --upgrade pip==24.0 setuptools==69.5.1 wheel==0.43.0 --quiet
echo       Done.

:: ── Step 5: Install numpy FIRST (torch depends on it at build time) ──────────
echo.
echo [5/7] Installing numpy first (torch build dependency)...
pip install numpy==1.26.4 --quiet
echo       Done.

:: ── Step 6: Install all packages ─────────────────────────────────────────────
echo.
echo [6/7] Installing all packages from requirements.txt...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo ERROR: Installation failed. Check output above.
    pause & exit /b 1
)
echo       Done.

:: ── Step 7: Verify ───────────────────────────────────────────────────────────
echo.
echo [7/7] Running environment verification...
echo.
python verify_env.py
if errorlevel 1 (
    echo.
    echo ❌ Verification failed. Check errors above.
    pause & exit /b 1
)

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║  ✅ Environment ready!                               ║
echo ║                                                      ║
echo ║  To run the app:                                     ║
echo ║    venv\Scripts\activate                             ║
echo ║    streamlit run app.py                              ║
echo ╚══════════════════════════════════════════════════════╝
echo.
pause
