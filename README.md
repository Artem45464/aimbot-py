# Aimbot

## Overview
This project is an aimbot designed to detect and target specific colors on the screen. The bot captures the screen, processes the image to detect the target's color, and moves the mouse to the target's position for precise aiming.

## Features
- Toggle-based continuous scanning system
- Region-based tracking for improved performance
- Multi-color target detection with adjustable tolerance
- Headshot targeting for maximum effectiveness
- Precise mouse movement (no clicking)
- Separate keys for scanning and manual aiming

## How to Use
1. Run the program: `python main.py`
2. Press 'y' followed by Enter to toggle continuous scanning on/off
3. Press 'a' followed by Enter to manually aim at the last found target
4. Press 'q' followed by Enter to exit the program

When scanning is active, the aimbot will:
- Continuously scan for targets of the specified color
- Automatically aim at targets when found
- Focus on regions where targets were previously detected for better performance

## Target Color Configuration
The default configuration targets red colors. You can modify the `TARGET_COLORS` list in the code to detect different colors based on your needs:

```python
TARGET_COLORS = [
    (255, 0, 0),    # Red
    (240, 10, 10),  # Slightly different red
    (220, 0, 0)     # Darker red
]
```

You can also adjust `COLOR_TOLERANCE` (default: 75) to make the detection more or less sensitive.

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
