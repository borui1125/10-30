@echo off
setlocal
cd /d "%~dp0"
title Event Registration Backend

set "PYTHON=%~dp0.venv-runtime\Scripts\python.exe"

if not exist "%PYTHON%" (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -m venv "%~dp0.venv-runtime"
    ) else (
        where python >nul 2>nul
        if errorlevel 1 goto no_python
        python -m venv "%~dp0.venv-runtime"
    )
    if errorlevel 1 goto venv_failed
)

if not exist "%PYTHON%" goto venv_failed

"%PYTHON%" -c "import fastapi, uvicorn, sqlalchemy, psycopg, jinja2, dotenv, multipart" >nul 2>nul
if errorlevel 1 (
    echo Installing backend dependencies...
    "%PYTHON%" -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 goto install_failed
)

if not exist "%~dp0.env" (
    copy "%~dp0.env.example" "%~dp0.env" >nul
    echo Created .env from .env.example.
    echo Enter the PostgreSQL password in the editor, save the file, then run this file again.
    start "" notepad "%~dp0.env"
    pause
    exit /b 1
)

"%PYTHON%" -c "from dotenv import dotenv_values; from urllib.parse import urlsplit; import sys; u=dotenv_values(r'%~dp0.env').get('DATABASE_URL', ''); p=urlsplit(u); sys.exit(0 if p.scheme in ('postgresql', 'postgresql+psycopg') and p.hostname and p.username and p.password and p.path.strip('/') and 'your_password' not in u and '******' not in u else 1)" >nul 2>nul
if errorlevel 1 (
    echo .env is missing a valid PostgreSQL DATABASE_URL or still has the sample password.
    echo Set DATABASE_URL to postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
    start "" notepad "%~dp0.env"
    pause
    exit /b 1
)

echo Starting backend at http://127.0.0.1:8000/
start "" "http://127.0.0.1:8000/"
"%PYTHON%" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

echo.
echo Backend stopped. Check the error above if it did not start.
pause
exit /b

:no_python
echo Python was not found. Install Python 3.12 or newer and try again.
pause
exit /b 1

:venv_failed
echo Could not create the Python virtual environment.
pause
exit /b 1

:install_failed
echo Could not install dependencies. Check your internet connection and requirements.txt.
pause
exit /b 1
