# Cross-Platform Aimbot

A simple color-based aimbot that works on Windows, macOS, and Linux.

## Quick Start

### Windows
Double-click `windows_run.bat`

### macOS
1. Open Terminal
2. Drag and drop `mac_run.command` into the Terminal window
3. Press Enter

### Linux
1. Open Terminal
2. Navigate to the aimbot directory
3. Run: `./linux_run.sh`

## Manual Installation

If the quick start scripts don't work:

1. Install Python 3.6 or higher
2. Create a virtual environment:
   ```
   python -m venv .venv
   ```
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run the script:
   ```
   python main.py
   ```

## Controls
- Press 'y' to toggle continuous scanning on/off
- Press 'a' to aim at the last found target
- Press 'q' to exit

## Configuration
You can modify the following settings in `main.py`:
- `TARGET_COLORS`: List of RGB colors to detect
- `COLOR_TOLERANCE`: How much color variation to allow
- `MIN_CONTOUR_AREA`: Minimum size of targets to detect
- `SCAN_KEY`, `AIM_KEY`, `EXIT_KEY`: Keyboard controls