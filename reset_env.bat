@echo off
echo.
echo ══════════════════════════════════════════════
echo  Steel Defect Pro — Environment Reset Script
echo ══════════════════════════════════════════════
echo.

echo [1/5] Uninstalling conflicting packages...
pip uninstall -y torch torchvision torchaudio numpy opencv-python opencv-python-headless ultralytics streamlit pillow pandas plotly firebase-admin 2>nul
echo Done.

echo.
echo [2/5] Clearing pip cache...
pip cache purge
echo Done.

echo.
echo [3/5] Upgrading pip, setuptools, wheel...
python -m pip install --upgrade pip setuptools wheel
echo Done.

echo.
echo [4/5] Installing all packages from requirements.txt...
pip install -r requirements.txt
echo Done.

echo.
echo [5/5] Verifying environment...
python verify_env.py

echo.
echo ══════════════════════════════════════════════
echo  If all checks passed, run:  streamlit run app.py
echo ══════════════════════════════════════════════
pause
