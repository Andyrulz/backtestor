@echo off
echo 🧪 Testing Virtual Environment Setup
echo ====================================

cd /d "%~dp0"

echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    echo.
    echo 💡 Virtual environment setup steps:
    echo    1. python -m venv venv
    echo    2. venv\Scripts\activate.bat
    echo    3. pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo ✅ Virtual environment activated successfully!
echo.

echo 🔍 Checking Python and packages...
python --version
echo.

echo 📦 Checking Streamlit...
python -c "import streamlit; print(f'Streamlit version: {streamlit.__version__}')"
if errorlevel 1 (
    echo ❌ Streamlit not found
    echo 💡 Run: pip install streamlit
    pause
    exit /b 1
)

echo 📦 Checking KiteConnect...
python -c "import kiteconnect; print('KiteConnect available')"
if errorlevel 1 (
    echo ❌ KiteConnect not found
    echo 💡 Run: pip install kiteconnect
    pause
    exit /b 1
)

echo.
echo ✅ All dependencies available!
echo 🎯 Ready to run the trading app!
echo.
echo 🚀 To start the app, run: start_auto_auth.bat
echo.

pause
