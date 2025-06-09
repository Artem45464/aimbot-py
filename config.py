"""
Configuration management for the aimbot.
Handles saving, loading, and modifying configuration settings.
"""
import os
import json
import platform

# Default configuration file path based on platform
if platform.system() == 'Windows':
    DEFAULT_CONFIG_PATH = os.path.join(os.path.expanduser('~'), 'aimbot_config.json')
else:  # macOS and Linux
    DEFAULT_CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.aimbot_config.json')

# Default configuration settings
DEFAULT_CONFIG = {
    'target_colors': [
        # Red colors
        [255, 0, 0],    # Pure red
        [240, 10, 10],  # Slightly different red
        [220, 0, 0],    # Darker red
        [255, 50, 50],  # Light red
        [200, 0, 0],    # Very dark red
        [255, 100, 100], # Pink-red
        
        # Green colors
        [0, 255, 0],    # Pure green
        [0, 220, 0],    # Darker green
        [50, 255, 50],  # Light green
        [0, 200, 0],    # Very dark green
        [100, 255, 100], # Light green
        
        # Blue colors
        [0, 0, 255],    # Pure blue
        [0, 0, 220],    # Darker blue
        [50, 50, 255],  # Light blue
        [0, 0, 200],    # Very dark blue
        [100, 100, 255], # Light blue
        
        # Yellow colors
        [255, 255, 0],  # Pure yellow
        [220, 220, 0],  # Darker yellow
        [255, 255, 50], # Light yellow
        
        # Purple/Magenta colors
        [255, 0, 255],  # Pure magenta
        [220, 0, 220],  # Darker magenta
        [255, 50, 255], # Light magenta
        [180, 0, 180],  # Dark purple
        
        # Cyan colors
        [0, 255, 255],  # Pure cyan
        [0, 220, 220],  # Darker cyan
        [50, 255, 255], # Light cyan
        
        # Orange colors
        [255, 165, 0],  # Pure orange
        [255, 140, 0],  # Dark orange
        [255, 190, 0],  # Light orange
        
        # White/Gray colors (for white targets)
        [255, 255, 255], # Pure white
        [220, 220, 220], # Light gray
        [200, 200, 200], # Medium gray
        
        # Black colors
        [0, 0, 0],      # Pure black
        [20, 20, 20],   # Near black
        [40, 40, 40]    # Dark gray
    ],
    'color_priority': {
        'red': 10,      # Highest priority
        'green': 3,
        'blue': 3,
        'yellow': 6,
        'purple': 4,
        'cyan': 2,
        'orange': 8,
        'white': 1,     # Lowest priority
        'black': 5      # Medium priority
    },
    'use_color_priority': False,  # Disabled by default
    'toggle_priority_key': 't',   # Key to toggle priority targeting
    'color_tolerance': 60,
    'min_contour_area': 15,
    'scan_key': 'y',
    'aim_key': 'f',
    'exit_key': 'q',
    'save_config_key': 'o',
    'load_config_key': 'p',
    'headshot_percentage': 0.10,  # Target the top 10% of the contour
    'aim_delay': 0.0,  # Delay in seconds before aiming at target (0 = no delay)
    'auto_fire': False,  # Whether to automatically fire when aiming at a target
    'dynamic_area': True,  # Whether to dynamically adjust contour area based on target size
    'prediction_strength': 100,  # Strength of movement prediction (0-100%)
    'accel_compensation': 50,  # Acceleration compensation percentage (0-100%)
    'latency_compensation': 50  # System latency compensation in ms (0-100ms)
}

def load_config(config_path=None):
    """
    Load configuration from a JSON file.
    
    Args:
        config_path (str, optional): Path to the config file. If None, uses the default path.
        
    Returns:
        dict: The loaded configuration, or the default configuration if loading fails.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
        
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Ensure all required keys are present by merging with defaults
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
                    
            return config
        else:
            print(f"Config file not found at {config_path}. Using default configuration.")
            return DEFAULT_CONFIG.copy()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        print("Using default configuration.")
        return DEFAULT_CONFIG.copy()

def save_config(config, config_path=None):
    """
    Save configuration to a JSON file.
    
    Args:
        config (dict): The configuration to save.
        config_path (str, optional): Path to the config file. If None, uses the default path.
        
    Returns:
        bool: True if saving was successful, False otherwise.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
        
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False

def print_config(config):
    """
    Print the current configuration in a readable format.
    
    Args:
        config (dict): The configuration to print.
    """
    print("\n=== Current Configuration ===")
    print(f"Color Tolerance: {config['color_tolerance']}")
    print(f"Minimum Contour Area: {config['min_contour_area']}")
    print(f"Dynamic Area Adjustment: {'Enabled' if config.get('dynamic_area', True) else 'Disabled'}")
    print(f"Headshot Percentage: {config['headshot_percentage'] * 100}%")
    print(f"Aim Delay: {config['aim_delay']}s")
    print(f"Auto Fire: {'Enabled' if config.get('auto_fire', False) else 'Disabled'}")
    
    # Advanced targeting settings
    print("\nAdvanced Targeting:")
    print(f"Prediction Strength: {config.get('prediction_strength', 100)}%")
    print(f"Acceleration Compensation: {config.get('accel_compensation', 50)}%")
    print(f"Latency Compensation: {config.get('latency_compensation', 50)}ms")
    
    # Target priority settings
    print("\nTarget Priority:")
    print(f"Priority-based Targeting: {'Enabled' if config.get('use_color_priority', False) else 'Disabled'}")
    print(f"Toggle Priority Key: '{config.get('toggle_priority_key', 't')}'")
    if 'color_priority' in config:
        priorities = sorted(config['color_priority'].items(), key=lambda x: x[1], reverse=True)
        print("Color Priorities (high to low):")
        for color, priority in priorities:
            print(f"  {color.capitalize()}: {priority}")
    
    print("\nKeyboard Controls:")
    print(f"Scan Toggle: '{config['scan_key']}'")
    print(f"Aim: '{config['aim_key']}'")
    print(f"Exit: '{config['exit_key']}'")
    print(f"Save Config: '{config['save_config_key']}'")
    print(f"Load Config: '{config['load_config_key']}'")
    print(f"Number of Target Colors: {len(config['target_colors'])}")
    print("============================\n")

def modify_config(config):
    """
    Interactive menu to modify configuration settings.
    
    Args:
        config (dict): The current configuration.
        
    Returns:
        dict: The modified configuration.
    """
    print("\n=== Configuration Menu ===")
    print("1. Change color tolerance")
    print("2. Change minimum contour area")
    print("3. Toggle dynamic area adjustment")
    print("4. Change headshot percentage")
    print("5. Change aim delay")
    print("6. Toggle auto fire")
    print("7. Change keyboard controls")
    print("8. Advanced targeting settings")
    print("9. Configure target priorities")
    print("10. Configure toggle priority key")
    print("11. Reset to defaults")
    print("0. Back to main menu")
    
    choice = input("Enter your choice (0-11): ")
    
    if choice == '1':
        try:
            value = int(input(f"Enter new color tolerance (current: {config['color_tolerance']}): "))
            if 0 <= value <= 255:
                config['color_tolerance'] = value
                print(f"Color tolerance set to {value}")
            else:
                print("Value must be between 0 and 255")
        except ValueError:
            print("Invalid input. Please enter a number.")
            
    elif choice == '2':
        try:
            value = int(input(f"Enter new minimum contour area (current: {config['min_contour_area']}): "))
            if value > 0:
                config['min_contour_area'] = value
                print(f"Minimum contour area set to {value}")
            else:
                print("Value must be greater than 0")
        except ValueError:
            print("Invalid input. Please enter a number.")
            
    elif choice == '3':
        dynamic_area = config.get('dynamic_area', True)
        new_setting = not dynamic_area
        config['dynamic_area'] = new_setting
        print(f"Dynamic area adjustment {'enabled' if new_setting else 'disabled'}")
            
    elif choice == '4':
        try:
            value = float(input(f"Enter new headshot percentage (current: {config['headshot_percentage'] * 100}%): "))
            if 0 < value <= 100:
                config['headshot_percentage'] = value / 100
                print(f"Headshot percentage set to {value}%")
            else:
                print("Value must be between 0 and 100")
        except ValueError:
            print("Invalid input. Please enter a number.")
            
    elif choice == '5':
        try:
            value = float(input(f"Enter new aim delay in seconds (current: {config['aim_delay']}): "))
            if value >= 0:
                config['aim_delay'] = value
                print(f"Aim delay set to {value} seconds")
            else:
                print("Value must be 0 or greater")
        except ValueError:
            print("Invalid input. Please enter a number.")
            
    elif choice == '6':
        auto_fire = config.get('auto_fire', False)
        new_setting = not auto_fire
        config['auto_fire'] = new_setting
        print(f"Auto fire {'enabled' if new_setting else 'disabled'}")
            
    elif choice == '7':
        print("\n=== Keyboard Controls ===")
        print("1. Change scan toggle key")
        print("2. Change aim key")
        print("3. Change exit key")
        print("4. Change save config key")
        print("5. Change load config key")
        print("6. Back to config menu")
        
        key_choice = input("Enter your choice (1-6): ")
        
        if key_choice == '1':
            key = input(f"Enter new scan toggle key (current: '{config['scan_key']}'): ")
            if key and len(key) == 1:
                config['scan_key'] = key.lower()
                print(f"Scan toggle key set to '{key.lower()}'")
            else:
                print("Invalid key. Please enter a single character.")
                
        elif key_choice == '2':
            key = input(f"Enter new aim key (current: '{config['aim_key']}'): ")
            if key and len(key) == 1:
                config['aim_key'] = key.lower()
                print(f"Aim key set to '{key.lower()}'")
            else:
                print("Invalid key. Please enter a single character.")
                
        elif key_choice == '3':
            key = input(f"Enter new exit key (current: '{config['exit_key']}'): ")
            if key and len(key) == 1:
                config['exit_key'] = key.lower()
                print(f"Exit key set to '{key.lower()}'")
            else:
                print("Invalid key. Please enter a single character.")
                
        elif key_choice == '4':
            key = input(f"Enter new save config key (current: '{config['save_config_key']}'): ")
            if key and len(key) == 1:
                config['save_config_key'] = key.lower()
                print(f"Save config key set to '{key.lower()}'")
            else:
                print("Invalid key. Please enter a single character.")
                
        elif key_choice == '5':
            key = input(f"Enter new load config key (current: '{config['load_config_key']}'): ")
            if key and len(key) == 1:
                config['load_config_key'] = key.lower()
                print(f"Load config key set to '{key.lower()}'")
            else:
                print("Invalid key. Please enter a single character.")
    
    elif choice == '8':
        print("\n=== Advanced Targeting Settings ===")
        print("1. Configure prediction strength (0-100%)")
        print("2. Configure acceleration compensation (0-100%)")
        print("3. Configure system latency compensation (0-100ms)")
        print("4. Back to main menu")
        
        adv_choice = input("Enter your choice (1-4): ")
        
        if adv_choice == '1':
            try:
                current = config.get('prediction_strength', 100)
                value = int(input(f"Enter prediction strength percentage (current: {current}%): "))
                if 0 <= value <= 100:
                    config['prediction_strength'] = value
                    print(f"Prediction strength set to {value}%")
                else:
                    print("Value must be between 0 and 100")
            except ValueError:
                print("Invalid input. Please enter a number.")
                
        elif adv_choice == '2':
            try:
                current = config.get('accel_compensation', 50)
                value = int(input(f"Enter acceleration compensation percentage (current: {current}%): "))
                if 0 <= value <= 100:
                    config['accel_compensation'] = value
                    print(f"Acceleration compensation set to {value}%")
                else:
                    print("Value must be between 0 and 100")
            except ValueError:
                print("Invalid input. Please enter a number.")
                
        elif adv_choice == '3':
            try:
                current = config.get('latency_compensation', 50)
                value = int(input(f"Enter system latency compensation in ms (current: {current}ms): "))
                if 0 <= value <= 100:
                    config['latency_compensation'] = value
                    print(f"System latency compensation set to {value}ms")
                else:
                    print("Value must be between 0 and 100")
            except ValueError:
                print("Invalid input. Please enter a number.")
    
    elif choice == '9':
        print("\n=== Target Priority Configuration ===")
        print("Configure which colors should be prioritized when multiple targets are detected.")
        print("Higher values = higher priority (1-10)")
        
        # Initialize color priority if it doesn't exist
        if 'color_priority' not in config:
            config['color_priority'] = {
                'red': 10,      # Highest priority
                'green': 3,
                'blue': 3,
                'yellow': 6,
                'purple': 4,
                'cyan': 2,
                'orange': 8,
                'white': 1,     # Lowest priority
                'black': 5      # Medium priority
            }
        # Make sure black is included in color priorities
        if 'black' not in config['color_priority']:
            config['color_priority']['black'] = 5
        
        # Show current priorities
        print("\nCurrent priorities:")
        for color, priority in config['color_priority'].items():
            print(f"{color.capitalize()}: {priority}")
        
        # Allow user to modify priorities
        print("\nEnter new priority values (1-10) or press Enter to keep current value:")
        
        # Sort colors by current priority for better UX
        sorted_colors = sorted(config['color_priority'].items(), key=lambda x: x[1], reverse=True)
        
        for color, current in sorted_colors:
            try:
                value = input(f"{color.capitalize()} (current: {current}): ")
                if value.strip():
                    value = int(value)
                    if 1 <= value <= 10:
                        config['color_priority'][color] = value
                        print(f"{color.capitalize()} priority set to {value}")
                    else:
                        print("Value must be between 1 and 10")
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        # Ask if user wants to enable priority-based targeting
        current_setting = config.get('use_color_priority', False)
        enable = input(f"\nEnable priority-based targeting? (y/n) [current: {'y' if current_setting else 'n'}]: ")
        
        if enable.strip():
            config['use_color_priority'] = enable.lower() == 'y'
        
        # Show target selection strategy based on setting
        if config['use_color_priority']:
            print("\nPriority-based targeting enabled")
            print("Target selection strategy: Will prioritize targets by color according to priority values")
            print("Highest priority colors: " + ", ".join([c.capitalize() for c, p in sorted(config['color_priority'].items(), key=lambda x: x[1], reverse=True)[:3]]))
        else:
            print("\nPriority-based targeting disabled")
            print("Target selection strategy: Will select the largest target regardless of color")
            
    elif choice == '10':
        # Configure toggle priority key
        if 'toggle_priority_key' not in config:
            config['toggle_priority_key'] = 't'  # Default key
            
        key = input(f"Enter new toggle priority key (current: '{config.get('toggle_priority_key', 't')}'): ")
        if key and len(key) == 1:
            config['toggle_priority_key'] = key.lower()
            print(f"Toggle priority key set to '{key.lower()}'")
        else:
            print("Invalid key. Please enter a single character.")
            
    elif choice == '11':
        confirm = input("Are you sure you want to reset to default settings? (y/n): ")
        if confirm.lower() == 'y':
            print("Configuration reset to defaults.")
            return DEFAULT_CONFIG.copy()
            
    elif choice == '0':
        print("Returning to main menu.")
    
    return config
