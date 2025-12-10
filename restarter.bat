@echo off
echo Stopping all Python processes...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
echo All Python processes stopped.

echo Starting main_clean.py...
python main_clean.py

echo Script execution completed.
pause
