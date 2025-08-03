@echo off
echo 🚀 Quick Start - Kite Trading System
echo ===================================

cd /d "%~dp0"

echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    echo 💡 Try running: python -m venv venv
    echo 💡 Then: venv\Scripts\activate.bat
    echo 💡 Then: pip install -r requirements.txt
    pause
    exit /b 1
)

echo ✅ Virtual environment activated
echo 🌐 Starting Streamlit app...
echo 💡 App will be available at: http://localhost:8501
echo 🔐 Automatic authentication enabled
echo.

streamlit run src\app.py --server.port=8501

pause
