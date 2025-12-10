@echo off
REM Database utility scripts for Windows

echo Database Utilities
echo ==================
echo.
echo Available commands:
echo   clean    - Clean all database tables (truncate)
echo   init     - Initialize all database tables
echo   check    - Check database status
echo.
echo Usage: db_utils.bat [command]
echo.

if "%1"=="clean" goto clean
if "%1"=="init" goto init
if "%1"=="check" goto check

echo Please specify a command: clean, init, or check
goto end

:clean
echo Cleaning database...
python clean_db.py
goto end

:init
echo Initializing database...
python init_db.py
goto end

:check
echo Checking database status...
set PGPASSWORD=app_password
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5432 -U app_user -d supreme_octosuccotash_db -c "SELECT relname as table_name, n_live_tup as live_rows FROM pg_stat_user_tables ORDER BY n_live_tup DESC;"
goto end

:end
