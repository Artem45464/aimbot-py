#!/bin/bash
cd "$(dirname "$0")"

# Make the script executable
chmod +x "$0"

echo "Starting aimbot on macOS..."

# Check Python version (must be 3.6 or higher)
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 6) else 1)" || {
    echo "Error: Python 3.6 or higher is required."
    echo "Current Python version: $(python3 --version)"
    read -p "Press Enter to exit..."
    exit 1
}

# Check for macOS permissions
if ! python3 -c "import pyautogui; pyautogui.position()" &>/dev/null; then
    echo "Error: Accessibility permissions may not be granted."
    echo "Please go to System Preferences > Security & Privacy > Privacy > Accessibility"
    echo "and add Terminal (or your IDE) to the list of allowed apps."
    read -p "Press Enter after granting permissions..."
    
    # Verify permissions after user confirmation
    if ! python3 -c "import pyautogui; pyautogui.position()" &>/dev/null; then
        echo "Warning: Accessibility permissions still appear to be missing."
        echo "The aimbot may not function correctly without these permissions."
        read -p "Press Enter to continue anyway..."
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv .venv || {
        echo "Failed to create virtual environment."
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
    
    # Install macOS-specific packages
    echo "Installing macOS-specific packages..."
    .venv/bin/pip install pyobjc-core pyobjc-framework-Quartz || {
        echo "Warning: Failed to install macOS-specific packages."
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
    .venv/bin/pip install pyobjc-core pyobjc-framework-Quartz || {
        echo "Warning: Failed to install macOS-specific packages."
        echo "Some features may not work correctly."
    }
fi

# Check for Quartz framework
if ! .venv/bin/python -c "from Quartz import CGPostMouseEvent" &>/dev/null; then
    echo "Warning: Quartz framework not found. Mouse movement may not work correctly."
    echo "Trying to install required packages..."
    .venv/bin/pip install pyobjc-core pyobjc-framework-Quartz
    
    # Verify installation was successful
    if ! .venv/bin/python -c "from Quartz import CGPostMouseEvent" &>/dev/null; then
        echo "Warning: Failed to install Quartz framework."
        echo "Mouse movement may not work correctly."
    fi
fi
.venv/bin/python main.py "$@"

# If we get here, the program has exited
read -p "Press Enter to exit..."
exit 0
