# Aimbot

## Overview
This project is an aimbot designed to detect and target specific colors on the screen. The bot captures the screen, processes the image to detect the target's color, and moves the mouse to the target's position for precise aiming.

## Features
- Manual activation system (only fires when you press 'y')
- Multi-color target detection with adjustable tolerance
- Headshot targeting for maximum effectiveness
- Precise mouse movement and clicking
- No automatic scanning or clicking - only acts when commanded

## How to Use
1. Run the program: `python main.py`
2. When you want to scan for targets and fire, press 'y' and hit Enter
3. To exit the program, press 'q' and hit Enter

## Target Color Configuration
The default configuration targets red colors. You can modify the `TARGET_COLORS` list in the code to detect different colors based on your needs.

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
```

## Disclaimer
This tool is for educational purposes only. Use responsibly and only in environments where such tools are permitted.
