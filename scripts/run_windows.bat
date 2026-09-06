@echo off
title Sentence Jigsaw
cd /d "%~dp0\.."
echo Launching Sentence Jigsaw...
py run_app.py || python run_app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Press any key to exit...
    pause > nul
)
