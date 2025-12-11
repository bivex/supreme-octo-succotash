@echo off
echo ========================================
echo   Telegram Bot Simple Restarter
echo ========================================
echo.

cd /d "%~dp0"

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create .env file with BOT_TOKEN and other settings
    pause
    exit /b 1
)

REM Load environment variables from .env file
for /f "tokens=*" %%i in (.env) do (
    set %%i
)

REM Check if BOT_TOKEN is set
if "%BOT_TOKEN%"=="" (
    echo ERROR: BOT_TOKEN not found in .env file!
    pause
    exit /b 1
)

echo Using BOT_TOKEN: %BOT_TOKEN:~0,10%...
echo.

echo Step 1: Deleting existing webhook (to ensure polling mode)...
curl -s -X POST "https://api.telegram.org/bot%BOT_TOKEN%/deleteWebhook" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Webhook deleted successfully (polling mode ready)
) else (
    echo ✗ Failed to delete webhook
)

echo.
echo Step 2: Starting Telegram bot in polling mode...
echo Press Ctrl+C to stop the bot
echo.

python bot.py --mode polling

echo.
echo Bot stopped.
pause
