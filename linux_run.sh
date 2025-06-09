#!/bin/bash

# Make the script executable
chmod +x "$0"

# Check if running as root (which is not recommended)
if [ "$(id -u)" -eq 0 ]; then
    echo "Warning: Running as root is not recommended."
    echo "The script will install dependencies with sudo when needed."
    read -p "Continue as root anyway? (y/n): " choice
    if [ "$choice" != "y" ] && [ "$choice" != "Y" ]; then
        echo "Exiting..."
        exit 0
    fi
fi

# Check for X11 display server (required for screen capture)
if [ -z "$DISPLAY" ]; then
    echo "Error: No display server detected. This application requires X11."
    echo "If you're using Wayland, please run with XWayland."
    read -p "Press Enter to exit..."
    exit 1
fi

# Check for Wayland and warn user
if [ -n "$WAYLAND_DISPLAY" ] || [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    echo "Warning: Wayland detected. This application works best with X11."
    echo "Some features may not work correctly under Wayland."
    echo "For best results, log out and select 'X11' or 'Xorg' session at login."
    read -p "Continue anyway? (y/n): " choice
    if [ "$choice" != "y" ] && [ "$choice" != "Y" ]; then
        echo "Exiting..."
        exit 0
    fi
fi

# Check if Python is installed
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 is not installed or not in PATH."
    echo "Please install Python 3.6 or higher."
    
    # Suggest installation command based on distribution
    if command -v apt-get &>/dev/null; then
        echo "Try: sudo apt-get install python3 python3-pip python3-venv"
    elif command -v dnf &>/dev/null; then
        echo "Try: sudo dnf install python3 python3-pip python3-virtualenv"
    elif command -v pacman &>/dev/null; then
        echo "Try: sudo pacman -S python python-pip"
    fi
    
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
    
    # Check for OpenCV system dependencies
    if ! .venv/bin/python -c "import cv2" &>/dev/null; then
        echo "Warning: OpenCV not working correctly. Installing system dependencies..."
        if command -v apt-get &>/dev/null; then
            sudo apt-get install -y libsm6 libxext6 libxrender-dev
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y libSM libXext libXrender
        fi
    }
    echo "Setup complete!"
fi

# Run the application using the virtual environment
echo "Starting aimbot..."
# Check if Python exists and works in the virtual environment
if [ ! -f ".venv/bin/python" ] || ! .venv/bin/python -c "import cv2, numpy, mss, pyautogui, pynput" &>/dev/null; then
    echo "Python interpreter not found or required packages missing. Recreating environment..."
    rm -rf .venv
    python3 -m venv .venv || {
        echo "Failed to recreate virtual environment."
        read -p "Press Enter to exit..."
        exit 1
    }
    
    # Install system dependencies first
    echo "Checking for system dependencies..."
    if command -v apt-get &>/dev/null; then
        echo "Debian/Ubuntu detected. Installing required system packages..."
        sudo apt-get update
        sudo apt-get install -y python3-dev python3-tk libsm6 libxext6 libxrender-dev
    elif command -v dnf &>/dev/null; then
        echo "Fedora/RHEL detected. Installing required system packages..."
        sudo dnf install -y python3-devel python3-tkinter libSM libXext libXrender
    elif command -v pacman &>/dev/null; then
        echo "Arch Linux detected. Installing required system packages..."
        sudo pacman -S --noconfirm python-pip tk libsm libxext libxrender
    fi
    
    # Now install Python packages
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
        
        # Try to install system X11 development packages
        if command -v apt-get &>/dev/null; then
            echo "Installing X11 development packages..."
            sudo apt-get install -y python3-xlib libx11-dev
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y python3-xlib libX11-devel
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm python-xlib libx11
        fi
        
        # Try installing again
        .venv/bin/pip install python-xlib --force-reinstall
        
        if ! .venv/bin/python -c "from Xlib import display" &>/dev/null; then
            echo "Warning: X11 Python bindings still not working."
        else
            echo "Successfully installed X11 Python bindings."
        fi
    else
        echo "Successfully installed X11 Python bindings."
    fi
fi

# Check for toggle priority key in config
if [ -f "$HOME/.aimbot_config.json" ]; then
    if ! grep -q "toggle_priority_key" "$HOME/.aimbot_config.json"; then
        echo "Updating configuration with toggle priority key..."
        # Add toggle_priority_key to config if missing
        sed -i 's/"use_color_priority": false/"use_color_priority": false,\n    "toggle_priority_key": "t"/' "$HOME/.aimbot_config.json" 2>/dev/null || true
        
        # If sed failed (macOS compatibility), try a different approach
        if ! grep -q "toggle_priority_key" "$HOME/.aimbot_config.json"; then
            # Create a temporary file with the updated content
            cat "$HOME/.aimbot_config.json" | awk '{
                if ($0 ~ /"use_color_priority": false/) {
                    print $0 ",";
                    print "    \"toggle_priority_key\": \"t\"";
                } else {
                    print $0;
                }
            }' > "$HOME/.aimbot_config.json.tmp"
            
            # Replace the original file if the temporary file was created successfully
            if [ -s "$HOME/.aimbot_config.json.tmp" ]; then
                mv "$HOME/.aimbot_config.json.tmp" "$HOME/.aimbot_config.json"
            else
                rm -f "$HOME/.aimbot_config.json.tmp"
            fi
        fi
    fi
fi

# Check for missing TOGGLE_PRIORITY_KEY in main.py
if grep -q "TOGGLE_PRIORITY_KEY = 't'" main.py && ! grep -q "TOGGLE_PRIORITY_KEY = CONFIG.get('toggle_priority_key', 't')" main.py; then
    echo "Fixing TOGGLE_PRIORITY_KEY definition in main.py..."
    sed -i 's/TOGGLE_PRIORITY_KEY = .t./TOGGLE_PRIORITY_KEY = CONFIG.get(\"toggle_priority_key\", \"t\")/' main.py 2>/dev/null || true
fi

# Run the application
.venv/bin/python main.py "$@"

# If we get here, the program has exited
read -p "Press Enter to exit..."
exit 0
