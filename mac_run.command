#!/bin/bash
cd "$(dirname "$0")"

# Make the script executable
chmod +x "$0"

echo "Starting aimbot on macOS..."

# Check for macOS permissions
if ! python3 -c "import pyautogui" &>/dev/null; then
    echo "Error: Accessibility permissions may not be granted."
    echo "Please go to System Preferences > Security & Privacy > Privacy > Accessibility"
    echo "and add Terminal (or your IDE) to the list of allowed apps."
    read -p "Press Enter after granting permissions..."
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

# Check for Quartz framework
if ! .venv/bin/python -c "from Quartz import CGDisplayBounds" &>/dev/null; then
    echo "Warning: Quartz framework not found. Mouse movement may not work correctly."
    echo "Trying to install required packages..."
    .venv/bin/pip install pyobjc-core pyobjc-framework-Quartz
fi

# Run the application using the virtual environment
echo "Starting aimbot..."
.venv/bin/python run.py

# If we get here, the program has exited
read -p "Press Enter to exit..."
exit 0
