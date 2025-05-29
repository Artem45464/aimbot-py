@echo off
echo Starting aimbot...

REM Check for admin rights
net session >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo Running with administrator privileges.
) else (
    echo Warning: Not running as administrator.
    echo Some features may not work correctly.
    echo Consider right-clicking and selecting "Run as administrator"
    timeout /t 3 >nul
)

REM Try to find Python in common locations
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python run.py
) else (
    where python3 >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        python3 run.py
    ) else (
        echo Python not found. Please install Python 3.
        echo Visit https://www.python.org/downloads/windows/
        pause
        exit /b 1
    )
)
pause
