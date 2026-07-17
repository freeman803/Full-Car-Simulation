@echo off
REM ---------------------------------------------------------------------------
REM Host the tire visualizer for the whole WiFi/LAN.
REM
REM   - Binds all network interfaces (--host 0.0.0.0) so other machines can reach it.
REM   - Uses port 80 so teammates browse to http://tire.visualizer/ with no :port.
REM   - Does NOT open a browser (a server has none).
REM
REM MUST be run as Administrator (port 80 is privileged on Windows).
REM Right-click this file -> "Run as administrator", or launch from an elevated
REM terminal. Press Ctrl+C in the window to stop.
REM ---------------------------------------------------------------------------
cd /d "%~dp0"
if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" tire_viz_app.py --host 0.0.0.0 --port 80 --no-browser %*
) else (
    python tire_viz_app.py --host 0.0.0.0 --port 80 --no-browser %*
)
pause
