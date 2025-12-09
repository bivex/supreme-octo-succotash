@echo off
echo Killing processes on port 5000...
set "found_process=0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
    echo Terminating process with PID %%a
    taskkill /F /PID %%a
    set "found_process=1"
)
if %found_process%==0 (
    echo No processes found listening on port 5000.
) else (
    echo Done.
)
