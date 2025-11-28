@echo off
:: CafeSentinel - One-Time Setup Script
:: Registers the WATCHDOG (SentinelService) in Task Scheduler.
:: This ensures the monitoring service starts at logon, which then launches the GUI.
:: Run this file as Administrator!

echo ==================================================
echo   CafeSentinel Monitor - Installation
echo ==================================================

:: Check for Admin rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Admin rights confirmed.
) else (
    echo [ERROR] Please Right-Click and "Run as Administrator"
    pause
    exit
)

:: Define Paths
:: This .bat file is in the CafeSentinel folder.
:: We want to launch: %~dp0SentinelService\SentinelService.exe

set "EXE_PATH=%~dp0SentinelService\SentinelService.exe"
set "TASK_NAME=CafeSentinelMonitor"

if not exist "%EXE_PATH%" (
    echo [ERROR] Could not find SentinelService.exe!
    echo Expected: %EXE_PATH%
    pause
    exit
)

echo.
echo Registering Task Scheduler Entry...
echo Task Name: %TASK_NAME%
echo Target:    %EXE_PATH%

:: Create Task
:: /sc ONLOGON = Run when user logs in
:: /rl HIGHEST = Run as Administrator (No UAC)
:: /f = Force overwrite if exists
schtasks /create /tn "%TASK_NAME%" /tr "'%EXE_PATH%'" /sc ONLOGON /rl HIGHEST /f

if %errorLevel% == 0 (
    echo.
    echo [SUCCESS] Installation Complete!
    echo The Watchdog Service will now start automatically when you log in.
    echo You can delete this script if you want.
) else (
    echo.
    echo [FAILED] Could not create task. See error above.
)

echo.
pause
