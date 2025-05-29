#!/bin/bash
cd "$(dirname "$0")"

echo "Starting aimbot on macOS..."

# Check for macOS permissions
if ! python3 -c "import pyautogui" &>/dev/null; then
    echo "Error: Accessibility permissions may not be granted."
    echo "Please go to System Preferences > Security & Privacy > Privacy > Accessibility"
    echo "and add Terminal (or your IDE) to the list of allowed apps."
    read -p "Press Enter after granting permissions..."
fi

# Check for Python 3
if command -v python3 &>/dev/null; then
    python3 run.py
elif command -v python &>/dev/null; then
    # Check if this is Python 3
    PY_VERSION=$(python --version 2>&1)
    if [[ $PY_VERSION == *"Python 3"* ]]; then
        python run.py
    else
        echo "Error: Python 3 not found. Please install Python 3."
        echo "Visit https://www.python.org/downloads/mac-osx/"
        read -p "Press Enter to exit..."
        exit 1
    fi
else
    echo "Error: Python not found. Please install Python 3."
    echo "Visit https://www.python.org/downloads/mac-osx/"
    read -p "Press Enter to exit..."
    exit 1
fi