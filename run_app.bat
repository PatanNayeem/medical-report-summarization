@echo off
title Medical Report Summarizer Server
echo ========================================================
echo   AI Medical Report Summarizer Web Application
echo ========================================================
echo.
cd /d "%~dp0"

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python app.py
) else (
    if exist "C:\Users\PATAN\anaconda3\python.exe" (
        "C:\Users\PATAN\anaconda3\python.exe" app.py
    ) else (
        echo Python executable not found in PATH or default path.
        echo Please ensure Python 3.10+ is installed.
        pause
    )
)
pause
