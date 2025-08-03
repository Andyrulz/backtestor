@echo off
echo 🚀 Starting Kite Trading System with Automatic Authentication
echo ============================================================

cd /d "%~dp0"

echo � Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    echo 💡 Please ensure virtual environment is set up correctly
    pause
    exit /b 1
)

echo ✅ Virtual environment activated
echo �🔍 Checking configuration...
python check_config.py
if errorlevel 1 (
    echo ❌ Configuration check failed
    pause
    exit /b 1
)

echo.
echo ✅ Configuration OK
echo 🌐 Starting Streamlit app...
echo.
echo 💡 The app will be available at: http://localhost:8501
echo 🔐 Automatic authentication will handle login redirects
echo.

streamlit run src\app.py --server.port=8501

pause
