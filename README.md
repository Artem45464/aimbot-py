# Aimbot

## Overview
This project is an aimbot designed to automatically target enemies on the screen based on a specified color. The bot captures the screen, processes the image to detect the target's color, and moves the mouse to the target's position for smooth and precise aiming.

## Features
- Real-time screen capture and image processing
- Dynamic color tolerance adjustment for target detection
- Target detection using the center of mass from contours
- Smooth mouse movement to reduce detection by anti-cheat systems
- Double-click feature for increased accuracy

## Requirements
To run the aimbot, you'll need the following dependencies:
- Python 3.x
- `pyautogui`
- `mss`
- `numpy`
- `opencv-python`

You can install the required dependencies using `pip`:
```bash
pip install pyautogui mss numpy opencv-python
