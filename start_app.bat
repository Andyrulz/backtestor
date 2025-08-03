@echo off
echo Starting Kite Trading System...

REM Set Python path to include src directory
set PYTHONPATH=%~dp0src;%PYTHONPATH%

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Streamlit
streamlit run src\app.py --server.port=8501

pause
