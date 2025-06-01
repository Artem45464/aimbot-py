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
    set PYTHON=python
    goto :setup_env
) else (
    where python3 >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PYTHON=python3
        goto :setup_env
    ) else (
        echo Python not found. Please install Python 3.
        echo Visit https://www.python.org/downloads/windows/
        pause
        exit /b 1
    )
)

:setup_env
echo Checking for virtual environment...

REM Create virtual environment if it doesn't exist
if not exist .venv\ (
    echo Setting up virtual environment...
    %PYTHON% -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
    
    echo Installing dependencies...
    .venv\Scripts\pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo Warning: Some dependencies may not have installed correctly.
    )
    
    echo Installing Windows-specific packages...
    .venv\Scripts\pip install pywin32
    if %ERRORLEVEL% NEQ 0 (
        echo Warning: Failed to install Windows-specific packages.
    )
    
    echo Setup complete!
)

REM Run the application using the virtual environment
echo Starting aimbot...
REM Check if Python exists in the virtual environment
if not exist .venv\Scripts\python.exe (
    echo Python interpreter not found in virtual environment. Recreating environment...
    rmdir /s /q .venv
    %PYTHON% -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
    .venv\Scripts\pip install pywin32
)
.venv\Scripts\python run.py

REM If we get here, the program has exited
pause
exit /b 0
