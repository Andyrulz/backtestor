@echo off
echo 🧪 Testing Client Fix with Virtual Environment
echo =============================================

cd /d "%~dp0"

echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

echo 🔍 Running client fix test...
python test_client_fix.py

pause
