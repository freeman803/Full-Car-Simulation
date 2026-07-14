@echo off
cd /d "%~dp0"
if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" tire_viz_app.py %*
) else (
    python tire_viz_app.py %*
)
pause
