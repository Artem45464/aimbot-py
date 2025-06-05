#!/bin/bash

# Make the script executable
chmod +x "$0"

# Check for X11 display server (required for screen capture)
if [ -z "$DISPLAY" ]; then
    echo "Error: No display server detected. This application requires X11."
    echo "If you're using Wayland, please run with XWayland."
    read -p "Press Enter to exit..."
    exit 1
fi

# Check Python version (must be 3.6 or higher)
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 6) else 1)" || {
    echo "Error: Python 3.6 or higher is required."
    echo "Current Python version: $(python3 --version)"
    read -p "Press Enter to exit..."
    exit 1
}

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv .venv || {
        echo "Failed to create virtual environment. Please install python3-venv package."
        read -p "Press Enter to exit..."
        exit 1
    }
    
    # Install dependencies
    echo "Installing dependencies..."
    .venv/bin/pip install -r requirements.txt || {
        echo "Failed to install dependencies."
        read -p "Press Enter to exit..."
        exit 1
    }
    
    # Install Linux-specific packages
    .venv/bin/pip install python-xlib || {
        echo "Warning: Failed to install Linux-specific packages."
        echo "Some features may not work correctly."
    }
    echo "Setup complete!"
fi

# Run the application using the virtual environment
echo "Starting aimbot..."
# Check if Python exists and works in the virtual environment
if [ ! -f ".venv/bin/python" ] || ! .venv/bin/python -c "import cv2, numpy, mss, pyautogui" &>/dev/null; then
    echo "Python interpreter not found or required packages missing. Recreating environment..."
    rm -rf .venv
    python3 -m venv .venv || {
        echo "Failed to recreate virtual environment."
        read -p "Press Enter to exit..."
        exit 1
    }
    .venv/bin/pip install -r requirements.txt || {
        echo "Failed to install dependencies."
        read -p "Press Enter to exit..."
        exit 1
    }
    .venv/bin/pip install python-xlib || {
        echo "Warning: Failed to install Linux-specific packages."
        echo "Some features may not work correctly."
    }
fi

# Check for X11 Python bindings
if ! .venv/bin/python -c "from Xlib import display" &>/dev/null; then
    echo "Warning: X11 Python bindings not found. Mouse movement may not work correctly."
    echo "Trying to install required packages..."
    .venv/bin/pip install python-xlib
    
    # Verify installation was successful
    if ! .venv/bin/python -c "from Xlib import display" &>/dev/null; then
        echo "Warning: Failed to install X11 Python bindings."
        echo "Mouse movement may not work correctly."
    fi
fi

# Run the application
.venv/bin/python main.py "$@"

# If we get here, the program has exited
read -p "Press Enter to exit..."
exit 0
