@echo off
echo ========================================
echo   Telegram Bot Restarter
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

REM Set webhook URL (you can customize this)
if "%WEBHOOK_URL%"=="" (
    set WEBHOOK_URL=https://gladsomely-unvitriolized-trudie.ngrok-free.dev/webhook
)

echo Using BOT_TOKEN: %BOT_TOKEN:~0,10%...
echo Using WEBHOOK_URL: %WEBHOOK_URL%
echo.

echo Step 1: Deleting existing webhook...
curl -s -X POST "https://api.telegram.org/bot%BOT_TOKEN%/deleteWebhook" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Webhook deleted successfully
) else (
    echo ✗ Failed to delete webhook
)
timeout /t 2 >nul

echo.
echo Step 2: Setting new webhook...
curl -s -X POST "https://api.telegram.org/bot%BOT_TOKEN%/setWebhook" -d "url=%WEBHOOK_URL%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Webhook set successfully
) else (
    echo ✗ Failed to set webhook
)
timeout /t 2 >nul

echo.
echo Step 3: Checking webhook status...
curl -s "https://api.telegram.org/bot%BOT_TOKEN%/getWebhookInfo" | findstr /C:"url" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Webhook is active
) else (
    echo ✗ Webhook status check failed
)

echo.
echo Step 4: Starting Telegram bot...
echo Press Ctrl+C to stop the bot
echo.

python bot.py --mode webhook --webhook-url %WEBHOOK_URL%

echo.
echo Bot stopped.
pause
