#!/usr/bin/env python3
"""
Alternative cross-platform launcher for the aimbot

This script provides an alternative way to run the aimbot directly with Python:
    python run.py              # Run the aimbot
    python run.py --config     # Open the configuration menu

The platform-specific launcher scripts (mac_run.command, linux_run.sh, windows_run.bat)
are the recommended way to run the application.
"""
import os
import sys
import platform
import subprocess

def main():
    # Check Python version
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required")
        print(f"Current Python version: {platform.python_version()}")
        sys.exit(1)
        
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not script_dir:  # Handle case where __file__ might not be available
        script_dir = os.getcwd()
    
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
        except Exception as e:
            print(f"Warning: Could not check admin status: {e}")
    
    # macOS-specific checks
    elif platform.system() == "Darwin":
        # Check for accessibility permissions
        try:
            import pyautogui
            # Actually test mouse position access to trigger permission dialogs
            pyautogui.position()
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
    
    # Check if virtual environment exists or is incomplete
    if not os.path.exists(venv_python) or not os.path.exists(os.path.join(script_dir, ".venv", "pyvenv.cfg")):
        print("Virtual environment not found or incomplete. Setting up environment...")
        setup_environment(script_dir)
        
    # Verify the environment was set up correctly
    if not os.path.exists(venv_python):
        print(f"Error: Python interpreter not found at {venv_python} after setup")
        print("Virtual environment setup failed. Please check for errors above.")
        sys.exit(1)
        
    # Run the main script with the virtual environment Python
    try:
        if not os.path.exists(main_script):
            print(f"Error: Main script not found at {main_script}")
            sys.exit(1)
        
        # Pass any command line arguments to the main script
        cmd = [venv_python, main_script]
        if len(sys.argv) > 1:
            cmd.extend(sys.argv[1:])
        
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"Error: The aimbot exited with code {result.returncode}")
            sys.exit(result.returncode)
    except Exception as e:
        print(f"Error running the script: {e}")
        sys.exit(1)

def setup_environment(script_dir):
    """Set up the virtual environment and install dependencies"""
    try:
        # Clean up any existing incomplete environment
        venv_dir = os.path.join(script_dir, ".venv")
        if os.path.exists(venv_dir) and not os.path.exists(os.path.join(venv_dir, "pyvenv.cfg")):
            print("Removing incomplete virtual environment...")
            try:
                if platform.system() == "Windows":
                    subprocess.run(["rmdir", "/s", "/q", venv_dir], check=False, shell=True)
                else:
                    subprocess.run(["rm", "-rf", venv_dir], check=False)
            except Exception as e:
                print(f"Warning: Could not remove existing environment: {e}")
                
        # Create virtual environment
        print("Creating virtual environment...")
        result = subprocess.run([sys.executable, "-m", "venv", venv_dir], check=False)
        if result.returncode != 0:
            print("Error: Failed to create virtual environment")
            sys.exit(1)
        
        # Install dependencies
        print("Installing dependencies...")
        if platform.system() == "Windows":
            pip = os.path.join(script_dir, ".venv", "Scripts", "pip")
            if not os.path.exists(pip):
                if os.path.exists(pip + ".exe"):
                    pip = pip + ".exe"
        else:  # macOS or Linux
            pip = os.path.join(script_dir, ".venv", "bin", "pip")
            
        try:
            print("Installing dependencies from requirements.txt...")
            result = subprocess.run([pip, "install", "-r", os.path.join(script_dir, "requirements.txt")], check=False)
            if result.returncode != 0:
                print("Warning: Some dependencies may not have installed correctly")
                
            # Verify critical dependencies
            venv_python = os.path.join(script_dir, ".venv", "bin", "python") if platform.system() != "Windows" else os.path.join(script_dir, ".venv", "Scripts", "python.exe")
            verify_cmd = [venv_python, "-c", "import cv2, numpy, mss, pyautogui, pynput"]
            verify_result = subprocess.run(verify_cmd, check=False)
            if verify_result.returncode != 0:
                print("Warning: Critical dependencies are missing. The aimbot may not work correctly.")
        except Exception as e:
            print(f"Error installing dependencies: {e}")
            print("Continuing anyway, but some features may not work correctly.")
        
        # Windows-specific packages
        if platform.system() == "Windows":
            try:
                result = subprocess.run([pip, "install", "pywin32"], check=False)
                if result.returncode == 0:
                    print("Installed Windows-specific packages")
                else:
                    print("Warning: Could not install Windows-specific packages")
            except Exception as e:
                print(f"Warning: Could not install Windows-specific packages: {e}")
        
        # macOS-specific packages
        elif platform.system() == "Darwin":
            try:
                result = subprocess.run([pip, "install", "pyobjc-core", "pyobjc-framework-Quartz"], check=False)
                if result.returncode == 0:
                    print("Installed macOS-specific packages")
                else:
                    print("Warning: Could not install macOS-specific packages")
            except Exception as e:
                print(f"Warning: Could not install macOS-specific packages: {e}")
                
        # Linux-specific packages
        elif platform.system() == "Linux":
            try:
                result = subprocess.run([pip, "install", "python-xlib"], check=False)
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
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
        sys.exit(1)
