#!/bin/bash

# Check for X11 display server (required for screen capture)
if [ -z "$DISPLAY" ]; then
    echo "Error: No display server detected. This application requires X11."
    echo "If you're using Wayland, please run with XWayland."
    read -p "Press Enter to exit..."
    exit 1
fi

# Try to find Python 3 in common locations
if command -v python3 &>/dev/null; then
    python3 run.py
elif command -v python &>/dev/null; then
    python run.py
else
    echo "Python not found. Please install Python 3."
    read -p "Press Enter to exit..."
    exit 1
fi