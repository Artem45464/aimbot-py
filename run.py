#!/usr/bin/env python3
"""
Cross-platform launcher for the aimbot
"""
import os
import sys
import platform
import subprocess

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Windows-specific checks
    if platform.system() == "Windows":
        # Check for admin rights
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            if not is_admin:
                print("Warning: Not running as administrator.")
                print("Some features may not work correctly.")
                print("Consider right-clicking and selecting 'Run as administrator'")
        except:
            pass
    
    # macOS-specific checks
    elif platform.system() == "Darwin":
        # Check for accessibility permissions
        try:
            import pyautogui
            # Just trying to use pyautogui will trigger permission dialogs if needed
        except ImportError:
            pass
        except Exception as e:
            print(f"Warning: {e}")
            print("You may need to grant accessibility permissions.")
            print("Go to System Preferences > Security & Privacy > Privacy > Accessibility")
            print("and add Terminal (or your IDE) to the list of allowed apps.")
            input("Press Enter to continue after granting permissions...")
    
    # Linux-specific checks
    elif platform.system() == "Linux":
        # Check for X11 display server
        if not os.environ.get('DISPLAY'):
            print("Error: No display server detected. This application requires X11.")
            print("If you're using Wayland, please run with XWayland.")
            input("Press Enter to exit...")
            sys.exit(1)
    
    # Path to the virtual environment Python interpreter
    if platform.system() == "Windows":
        venv_python = os.path.join(script_dir, ".venv", "Scripts", "python.exe")
    else:  # macOS or Linux
        venv_python = os.path.join(script_dir, ".venv", "bin", "python")
    
    # Path to the main script
    main_script = os.path.join(script_dir, "main.py")
    
    # Check if virtual environment exists
    if not os.path.exists(venv_python):
        print("Virtual environment not found. Setting up environment...")
        setup_environment(script_dir)
        
    # Run the main script with the virtual environment Python
    try:
        subprocess.run([venv_python, main_script])
    except Exception as e:
        print(f"Error running the script: {e}")
        sys.exit(1)

def setup_environment(script_dir):
    """Set up the virtual environment and install dependencies"""
    try:
        # Create virtual environment
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", os.path.join(script_dir, ".venv")])
        
        # Install dependencies
        print("Installing dependencies...")
        if platform.system() == "Windows":
            pip = os.path.join(script_dir, ".venv", "Scripts", "pip")
        else:  # macOS or Linux
            pip = os.path.join(script_dir, ".venv", "bin", "pip")
            
        try:
            result = subprocess.run([pip, "install", "-r", os.path.join(script_dir, "requirements.txt")], check=True)
            if result.returncode != 0:
                print("Warning: Some dependencies may not have installed correctly")
        except Exception as e:
            print(f"Error installing dependencies: {e}")
            print("Continuing anyway, but some features may not work correctly.")
        
        # Windows-specific packages
        if platform.system() == "Windows":
            try:
                result = subprocess.run([pip, "install", "pywin32"], check=True)
                if result.returncode == 0:
                    print("Installed Windows-specific packages")
                else:
                    print("Warning: Could not install Windows-specific packages")
            except Exception as e:
                print(f"Warning: Could not install Windows-specific packages: {e}")
        
        # macOS-specific packages
        elif platform.system() == "Darwin":
            try:
                result = subprocess.run([pip, "install", "pyobjc-core", "pyobjc-framework-Quartz"], check=True)
                if result.returncode == 0:
                    print("Installed macOS-specific packages")
                else:
                    print("Warning: Could not install macOS-specific packages")
            except Exception as e:
                print(f"Warning: Could not install macOS-specific packages: {e}")
                
        # Linux-specific packages
        elif platform.system() == "Linux":
            try:
                result = subprocess.run([pip, "install", "python-xlib"], check=True)
                if result.returncode == 0:
                    print("Installed Linux-specific packages")
                else:
                    print("Warning: Could not install Linux-specific packages")
            except Exception as e:
                print(f"Warning: Could not install Linux-specific packages: {e}")
                
        print("Setup complete!")
    except Exception as e:
        print(f"Error setting up environment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
