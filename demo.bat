
@echo off
title BoltTwin Demo

echo ========================================
echo        BoltTwin Prototype Demo
echo ========================================
echo.

echo Starting Backend...
start "BoltTwin Backend" cmd /k "cd /d C:\Users\Evapr\Downloads\BoltTwin_Prototype\boltwin\backend && venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo Starting Frontend...
start "BoltTwin Frontend" cmd /k "cd /d C:\Users\Evapr\Downloads\BoltTwin_Prototype\boltwin\frontend && python -m http.server 5173"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo        BoltTwin is starting...
echo ========================================
echo.
echo Dashboard: http://localhost:5173
echo API Docs:  http://localhost:8000/docs
echo.
echo Keep the two command windows open.
echo Close them when you are finished.
echo.

start http://localhost:5173

pause