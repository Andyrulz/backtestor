@echo off
echo 🚀 One-Command App Starter
echo =========================
cd /d "%~dp0"
call venv\Scripts\activate.bat && streamlit run src\app.py --server.port=8501
