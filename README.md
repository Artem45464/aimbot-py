# Cross-Platform Aimbot

A versatile color-based aimbot that works with virtually any game on Windows, macOS, and Linux.

## Quick Start

### Windows
Double-click `windows_run.bat`

### macOS
1. Open Terminal
2. Drag and drop `mac_run.command` into the Terminal window
3. Press Enter
4. Grant accessibility permissions when prompted (System Preferences > Security & Privacy > Privacy > Accessibility)

### Linux
1. Open Terminal
2. Navigate to the aimbot directory
3. Run: `./linux_run.sh`
   (The script will automatically make itself executable)

## Manual Installation

If the quick start scripts don't work:

1. Install Python 3.6 or higher
2. Create a virtual environment:
   ```
   python3 -m venv .venv
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
- Press 'f' to aim at the last found target
- Press 'q' to exit

## Configuration
You can modify the following settings in `main.py`:
- `TARGET_COLORS`: List of RGB colors to detect (now includes all common colors)
- `COLOR_TOLERANCE`: How much color variation to allow
- `MIN_CONTOUR_AREA`: Minimum size of targets to detect
- `SCAN_KEY`, `AIM_KEY`, `EXIT_KEY`: Keyboard controls

## Compatible Games
This aimbot works with virtually any game that displays targets on screen, including:
- First-person shooters (CS:GO, Valorant, Call of Duty)
- Third-person shooters (Fortnite, PUBG)
- MOBAs (League of Legends, Dota 2)
- Battle royale games
- Top-down shooters
- Browser-based games
- 2D platformers with enemies
- Racing games with colored opponents
- Sports games with highlighted players

## Features
- Multi-color target detection (red, green, blue, yellow, purple, cyan, orange, white)
- Enhanced image processing with contrast enhancement
- Precise headshot targeting (aims at the top 15% of targets)
- Adaptive region-based scanning for better performance
- Cross-platform support with optimized mouse movement for each OS
- Automatic dependency installation and environment setup

## Troubleshooting

### Virtual Environment Issues
If you see "Failed to resolve env" errors in your IDE:
```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Permission Issues
- **macOS**: Grant accessibility permissions in System Preferences > Security & Privacy > Privacy > Accessibility
- **Windows**: Run as administrator for full functionality
- **Linux**: Ensure X11 display server is running (Wayland is not supported)

### Dependencies
The launcher scripts will automatically install all required dependencies. If you encounter issues:
- **Windows**: Ensure you have Visual C++ build tools for pywin32
- **macOS**: You may need to install Command Line Tools with `xcode-select --install`
- **Linux**: Install python3-dev and python3-tk packages

## Disclaimer
Using this tool in online competitive games may violate terms of service and could result in account bans. It's best used for single-player games, practice modes, or custom games with friends who are aware you're using it.
