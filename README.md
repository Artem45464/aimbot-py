# Aimbot

## Overview
This project is an aimbot designed to automatically target enemies on the screen based on a specified color. The bot captures the screen, processes the image to detect the target's color, and moves the mouse to the target's position.

## Features
- Screen capture and real-time processing
- Dynamic color tolerance adjustment for target detection
- Target detection using center-of-mass from contours
- Smooth mouse movement to avoid detection by anti-cheat systems
- Double click for increased accuracy

## Requirements
- Python 3.x
- pyautogui
- mss
- numpy
- opencv-python



## Usage
1. After cloning the repository and installing the dependencies, open the script `aimbot.py` in your preferred IDE or editor.
2. Click the "Run" button to start the aimbot.
3. The script will run automatically, capturing the screen and detecting targets.
4. You can stop the aimbot anytime by pressing `Ctrl+C`.
