#!/bin/bash
cd "$(dirname "$0")"

# Make the script executable
chmod +x "$0"

# Fix script if it was edited on Windows (CRLF line endings)
if grep -q $'\r' "$0"; then
    echo "Fixing script line endings..."
    tr -d '\r' < "$0" > "$0.tmp" && mv "$0.tmp" "$0"
    chmod +x "$0"
    exec "$0" "$@"  # Re-execute the script with fixed line endings
    exit 0
fi

echo "Starting aimbot on macOS..."

# Check if Python 3 is installed
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 not found."
    echo "Please install Python 3.6 or higher from https://www.python.org/downloads/mac-osx/"
    echo "Or use Homebrew: brew install python3"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check Python version (must be 3.6 or higher)
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 6) else 1)" || {
    echo "Error: Python 3.6 or higher is required."
    echo "Current Python version: $(python3 --version)"
    echo "Please upgrade Python from https://www.python.org/downloads/mac-osx/"
    echo "Or use Homebrew: brew upgrade python3"
    read -p "Press Enter to exit..."
    exit 1
}

# Check if pyautogui is installed before checking permissions
if ! python3 -c "import sys; 'pyautogui' in sys.modules or sys.exit(1)" &>/dev/null; then
    echo "Installing pyautogui for permission check..."
    python3 -m pip install pyautogui --user
fi

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
    # First upgrade pip to avoid installation issues
    .venv/bin/pip install --upgrade pip
    
    # Install dependencies with timeout and retry logic
    max_attempts=3
    attempt=1
    success=false
    
    while [ $attempt -le $max_attempts ] && [ "$success" != "true" ]; do
        echo "Attempt $attempt of $max_attempts..."
        if .venv/bin/pip install -r requirements.txt; then
            success=true
        else
            echo "Attempt $attempt failed."
            if [ $attempt -lt $max_attempts ]; then
                echo "Waiting before retry..."
                sleep 3
            fi
            attempt=$((attempt+1))
        fi
    done
    
    if [ "$success" != "true" ]; then
        echo "Failed to install dependencies after $max_attempts attempts."
        read -p "Press Enter to exit..."
        exit 1
    fi
    
    # Install macOS-specific packages
    echo "Installing macOS-specific packages..."
    .venv/bin/pip install "pyobjc-core>=8.0,<10.0" "pyobjc-framework-Quartz>=8.0,<10.0" || {
        echo "Warning: Failed to install macOS-specific packages."
        echo "Some features may not work correctly."
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
    
    # Upgrade pip first
    .venv/bin/pip install --upgrade pip
    
    # Try installing with more robust error handling
    echo "Installing dependencies..."
    if ! .venv/bin/pip install -r requirements.txt; then
        echo "Standard installation failed. Trying alternative approach..."
        # Try installing packages one by one
        for package in numpy opencv-python mss pyautogui pynput; do
            echo "Installing $package..."
            .venv/bin/pip install $package || echo "Warning: Failed to install $package"
        done
    fi
fi

# Check for Quartz framework
if ! .venv/bin/python -c "from Quartz import CGPostMouseEvent" &>/dev/null; then
    echo "Warning: Quartz framework not found. Mouse movement may not work correctly."
    echo "Trying to install required packages..."
    
    # Check for Xcode Command Line Tools
    if ! xcode-select -p &>/dev/null; then
        echo "Xcode Command Line Tools not found. Installing..."
        xcode-select --install
        echo "Please wait for Xcode Command Line Tools installation to complete."
        echo "After installation completes, press Enter to continue."
        read -p "Press Enter after installation completes..."
    fi
    
    # Try installing with --no-cache-dir to avoid cached build issues
    .venv/bin/pip install --no-cache-dir pyobjc-core pyobjc-framework-Quartz
    
    # Verify installation was successful
    if ! .venv/bin/python -c "from Quartz import CGPostMouseEvent" &>/dev/null; then
        echo "Warning: Failed to install Quartz framework."
        echo "Mouse movement may not work correctly."
    else
        echo "Successfully installed Quartz framework."
    fi
fi

# Check for toggle priority key in config
if [ -f "$HOME/.aimbot_config.json" ]; then
    if ! grep -q "toggle_priority_key" "$HOME/.aimbot_config.json"; then
        echo "Updating configuration with toggle priority key..."
        # Use awk for reliable config update
        awk '{
            if ($0 ~ /"use_color_priority": false/) {
                print $0 ",";
                print "    \"toggle_priority_key\": \"t\"";
            } else {
                print $0;
            }
        }' "$HOME/.aimbot_config.json" > "$HOME/.aimbot_config.json.tmp"
        
        if [ -s "$HOME/.aimbot_config.json.tmp" ]; then
            mv "$HOME/.aimbot_config.json.tmp" "$HOME/.aimbot_config.json"
        else
            rm -f "$HOME/.aimbot_config.json.tmp"
        fi
    fi
fi

# Check macOS version for compatibility warnings
macos_version=$(sw_vers -productVersion)
if [[ "$macos_version" == 10.* ]]; then
    echo "Warning: Running on macOS 10.x ($macos_version)"
    echo "For best performance, macOS 11 (Big Sur) or newer is recommended."
    
    # Fix for older macOS versions
    if ! .venv/bin/python -c "import cv2" &>/dev/null; then
        echo "Attempting to fix OpenCV on older macOS..."
        .venv/bin/pip uninstall -y opencv-python
        .venv/bin/pip install opencv-python-headless
    fi
elif [[ "$macos_version" == 11.* || "$macos_version" == 12.* || "$macos_version" == 13.* || "$macos_version" == 14.* ]]; then
    echo "Running on compatible macOS version: $macos_version"
fi

# Check for missing TOGGLE_PRIORITY_KEY in main.py
if grep -q "TOGGLE_PRIORITY_KEY = 't'" main.py && ! grep -q "TOGGLE_PRIORITY_KEY = CONFIG.get('toggle_priority_key', 't')" main.py; then
    echo "Fixing TOGGLE_PRIORITY_KEY definition in main.py..."
    sed -i '' 's/TOGGLE_PRIORITY_KEY = .t./TOGGLE_PRIORITY_KEY = CONFIG.get("toggle_priority_key", "t")/' main.py 2>/dev/null || true
fi

.venv/bin/python main.py "$@"

# If we get here, the program has exited
read -p "Press Enter to exit..."
exit 0
