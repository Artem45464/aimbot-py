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
            
        subprocess.run([pip, "install", "-r", os.path.join(script_dir, "requirements.txt")])
        print("Setup complete!")
    except Exception as e:
        print(f"Error setting up environment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()