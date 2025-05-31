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
    .venv/bin/pip install python-xlib
    echo "Setup complete!"
fi

# Run the application using the virtual environment
echo "Starting aimbot..."
.venv/bin/python run.py

# If we get here, the program has exited
read -p "Press Enter to exit..."
exit 0
