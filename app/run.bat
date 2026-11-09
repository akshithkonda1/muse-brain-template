@echo off
REM Muse Brain launcher (Windows) — double-click to run the app.
REM Requires Python 3.10+ on PATH. No install, no admin rights.
cd /d "%~dp0.."
python app\app.py
pause
