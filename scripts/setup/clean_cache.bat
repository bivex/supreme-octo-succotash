@echo off
REM Clean Python cache files and directories
REM This script recursively removes all __pycache__ directories and .pyc files

echo Cleaning Python cache files...

REM Remove all __pycache__ directories recursively
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Remove all .pyc files recursively
for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f"

REM Remove all .pyo files recursively
for /r . %%f in (*.pyo) do @if exist "%%f" del /q "%%f"

REM Remove all .pyd files recursively (compiled extensions)
for /r . %%f in (*.pyd) do @if exist "%%f" del /q "%%f"

echo Cache cleanup completed!
echo.
pause
