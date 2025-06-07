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
- Press 'f' to aim at the last found target (auto-fires if enabled)
- Press 'o' to save current configuration
- Press 'p' to reload configuration
- Press 'q' to exit

## Configuration
You can now configure the aimbot in two ways:

### 1. Configuration Menu
Run the aimbot with the `--config` flag to open the configuration menu:
```
python main.py --config
```
This allows you to:
- Change color tolerance
- Adjust minimum contour area
- Toggle dynamic area adjustment for distant targets
- Set headshot targeting percentage
- Configure aim delay
- Toggle auto-fire functionality
- Customize keyboard controls
- Reset to default settings

### 2. Configuration File
The aimbot saves settings to a JSON configuration file:
- Windows: `%USERPROFILE%\aimbot_config.json`
- macOS/Linux: `~/.aimbot_config.json`

You can modify the following settings:
- `target_colors`: List of RGB colors to detect
- `color_tolerance`: How much color variation to allow
- `min_contour_area`: Minimum size of targets to detect
- `dynamic_area`: Whether to adjust contour area for distant targets
- `headshot_percentage`: Where to aim on targets (0.1 = top 10%)
- `aim_delay`: Delay in seconds before aiming (0 = no delay)
- `auto_fire`: Whether to automatically click when aiming
- `scan_key`, `aim_key`, `exit_key`, etc.: Keyboard controls

#### Advanced Settings
- `prediction_strength`: How aggressively to predict target movement (0-100%)
- `accel_compensation`: How much to compensate for target acceleration (0-100%)
- `latency_compensation`: System latency compensation in milliseconds (0-100ms)

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
- Precise headshot targeting (configurable targeting height)
- Dynamic area adjustment for targets at different distances
- Configurable aim delay for more natural movement
- Auto-fire option for one-click targeting and shooting
- Adaptive region-based scanning for better performance
- Cross-platform support with optimized mouse movement for each OS
- Automatic dependency installation and environment setup
- Customizable settings with save/load functionality
- Interactive configuration menu
- Silent operation mode with minimal console output

### Advanced Features
- **Intelligent Target Prediction**: Predicts target movement for more accurate shots
- **Bezier Curve Movement**: Natural, human-like mouse movement patterns
- **Adaptive Learning**: Improves accuracy based on hit/miss statistics
- **Hardware Optimization**: Automatically detects and optimizes for your system
- **Advanced Configuration**: Fine-tune prediction strength, acceleration compensation, and latency

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
