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
import json
import multiprocessing

def main():
    # Check Python version
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required")
        print(f"Current Python version: {platform.python_version()}")
        sys.exit(1)
        
    # Detect system capabilities for optimal performance
    detect_system_capabilities()
        
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
        
        # Add auto-optimization flag if no specific config is requested
        if len(sys.argv) > 1:
            cmd.extend(sys.argv[1:])
        else:
            # Auto-optimize based on detected system capabilities
            system_info_path = os.path.expanduser('~/.aimbot_system_info.json')
            if os.path.exists(system_info_path):
                try:
                    with open(system_info_path, 'r') as f:
                        system_info = json.load(f)
                    
                    # Add optimization flags based on system capabilities
                    if system_info.get("cpu_cores", 0) >= 8:
                        cmd.append("--optimize-cpu")
                    if system_info.get("memory", 0) >= 16:
                        cmd.append("--optimize-memory")
                    if "nvidia" in str(system_info.get("gpu", "")).lower():
                        cmd.append("--use-gpu")
                        
                    print("Auto-optimizing for your hardware...")
                except Exception as e:
                    print(f"Warning: Could not load system info for optimization: {e}")
        
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"Error: The aimbot exited with code {result.returncode}")
            sys.exit(result.returncode)
    except Exception as e:
        print(f"Error running the script: {e}")
        sys.exit(1)

# Detect system capabilities for optimal performance
def detect_system_capabilities():
    """Detect system capabilities and optimize settings for the current hardware"""
    system_info = {
        "os": platform.system(),
        "cpu_cores": multiprocessing.cpu_count(),
        "python_version": platform.python_version(),
        "memory": "unknown"
    }
    
    # Get memory info based on platform
    try:
        if platform.system() == "Windows":
            # Windows memory detection
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulonglong = ctypes.c_ulonglong
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', c_ulonglong),
                    ('ullAvailPhys', c_ulonglong),
                    ('ullTotalPageFile', c_ulonglong),
                    ('ullAvailPageFile', c_ulonglong),
                    ('ullTotalVirtual', c_ulonglong),
                    ('ullAvailVirtual', c_ulonglong),
                    ('ullExtendedVirtual', c_ulonglong),
                ]
            memoryStatus = MEMORYSTATUSEX()
            memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(memoryStatus))
            system_info["memory"] = memoryStatus.ullTotalPhys / (1024**3)  # Convert to GB
            
        elif platform.system() == "Linux":
            # Linux memory detection
            try:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if 'MemTotal' in line:
                            parts = line.split()
                            if len(parts) > 1:
                                system_info["memory"] = int(parts[1]) / (1024**2)  # Convert to GB
                            break
            except (IOError, ValueError, IndexError):
                system_info["memory"] = "unknown"
                        
        elif platform.system() == "Darwin":  # macOS
            # macOS memory detection
            try:
                output = subprocess.check_output(['sysctl', 'hw.memsize']).decode('utf-8')
                parts = output.split()
                if len(parts) > 1:
                    system_info["memory"] = int(parts[1]) / (1024**3)  # Convert to GB
            except (subprocess.SubprocessError, ValueError, IndexError):
                system_info["memory"] = "unknown"
    except Exception as e:
        print(f"Warning: Could not detect memory: {e}")
    
    # Detect GPU if possible
    try:
        if platform.system() == "Windows":
            try:
                output = subprocess.check_output(['wmic', 'path', 'win32_VideoController', 'get', 'name']).decode('utf-8')
                lines = output.strip().split('\n')
                if len(lines) > 1:
                    system_info["gpu"] = lines[1].strip()
                else:
                    system_info["gpu"] = "unknown"
            except (subprocess.SubprocessError, IndexError):
                system_info["gpu"] = "unknown"
        elif platform.system() == "Linux":
            try:
                output = subprocess.check_output(['lspci'], stderr=subprocess.STDOUT).decode('utf-8')
                for line in output.split('\n'):
                    if 'VGA' in line or '3D' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            system_info["gpu"] = parts[-1].strip()
                        else:
                            system_info["gpu"] = "unknown"
                        break
            except subprocess.SubprocessError:
                system_info["gpu"] = "unknown"
        elif platform.system() == "Darwin":
            try:
                output = subprocess.check_output(['system_profiler', 'SPDisplaysDataType']).decode('utf-8')
                for line in output.split('\n'):
                    if 'Chipset Model' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            system_info["gpu"] = parts[-1].strip()
                        else:
                            system_info["gpu"] = "unknown"
                        break
            except subprocess.SubprocessError:
                system_info["gpu"] = "unknown"
    except Exception:
        system_info["gpu"] = "unknown"
    
    # Save system info to a file for the aimbot to use
    config_dir = os.path.dirname(os.path.expanduser('~/.aimbot_config.json'))
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    
    system_info_path = os.path.expanduser('~/.aimbot_system_info.json')
    try:
        with open(system_info_path, 'w') as f:
            json.dump(system_info, f, indent=2)
        print(f"System capabilities detected: {system_info['os']}, {system_info['cpu_cores']} cores")
        
        # Optimize settings based on hardware
        if system_info["cpu_cores"] >= 8:
            print("High-performance CPU detected: Enabling advanced prediction")
        if system_info.get("memory", 0) >= 16:
            print("High memory detected: Enabling enhanced target tracking")
        if "nvidia" in str(system_info.get("gpu", "")).lower():
            print("NVIDIA GPU detected: Enabling GPU acceleration")
    except Exception as e:
        print(f"Warning: Could not save system info: {e}")

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
                
            # Verify critical dependencies using the pip path to determine the correct python path
            venv_python = pip.replace("pip", "python")
            if platform.system() == "Windows" and not venv_python.endswith(".exe"):
                venv_python += ".exe"
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
