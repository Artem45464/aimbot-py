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
    goto :check_version
) else (
    where python3 >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PYTHON=python3
        goto :check_version
    ) else (
        echo Python not found. Please install Python 3.6 or higher.
        echo Visit https://www.python.org/downloads/windows/
        pause
        exit /b 1
    )
)

:check_version
REM Check Python version (must be 3.6 or higher)
%PYTHON% -c "import sys; sys.exit(0 if sys.version_info >= (3, 6) else 1)" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python 3.6 or higher is required.
    for /f "tokens=*" %%i in ('%PYTHON% -c "import sys; print(\"Current Python version: \" + \".\".join(map(str, sys.version_info[:3])))"') do echo %%i
    pause
    exit /b 1
)
goto :setup_env

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
REM Check if Python exists in the virtual environment and required packages are installed
if not exist .venv\Scripts\python.exe (
    echo Python interpreter not found in virtual environment. Recreating environment...
    goto :recreate_env
)

REM Verify required packages are installed
.venv\Scripts\python -c "import cv2, numpy, mss, pyautogui" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Required packages missing. Recreating environment...
    goto :recreate_env
)
goto :run_app

:recreate_env
echo Recreating virtual environment...
rmdir /s /q .venv
%PYTHON% -m venv .venv
if %ERRORLEVEL% NEQ 0 (
    echo Failed to recreate virtual environment.
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

REM Verify the environment was recreated successfully
if not exist .venv\Scripts\python.exe (
    echo Error: Failed to recreate Python interpreter.
    pause
    exit /b 1
)

REM Verify required packages after recreation
.venv\Scripts\python -c "import cv2, numpy, mss, pyautogui" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Required packages still missing after environment recreation.
    echo Please try running the script again or install packages manually.
    pause
    exit /b 1
)

goto :run_app

:run_app
.venv\Scripts\python main.py %*

REM If we get here, the program has exited
pause
exit /b 0
