import pyautogui
import mss
import numpy as np
import cv2
import time
import sys
import platform
import os
import threading
import math
import ctypes  # Import ctypes at the top level for Windows

# Import macOS-specific modules at the top level if on macOS
if platform.system() == 'Darwin':
    try:
        from Quartz import CGDisplayBounds, CGMainDisplayID, CGPostMouseEvent, CGDisplayPixelsHigh
    except ImportError:
        print("Warning: Quartz framework not found. Mouse movement on macOS may not work correctly.")

from pynput import keyboard
import config  # Import the configuration module

# Load configuration
CONFIG = config.load_config()

# Configuration variables from config
TARGET_COLORS = [tuple(color) for color in CONFIG['target_colors']]
COLOR_TOLERANCE = CONFIG['color_tolerance']
MIN_CONTOUR_AREA = CONFIG['min_contour_area']
SCAN_KEY = CONFIG['scan_key']
AIM_KEY = CONFIG['aim_key']
EXIT_KEY = CONFIG['exit_key']
SAVE_CONFIG_KEY = CONFIG['save_config_key']
LOAD_CONFIG_KEY = CONFIG['load_config_key']
HEADSHOT_PERCENTAGE = CONFIG['headshot_percentage']

# Check for required dependencies
def check_dependencies():
    missing = []
    try:
        import pyautogui
    except ImportError:
        missing.append("pyautogui")
    
    try:
        import mss
    except ImportError:
        missing.append("mss")
        
    # Platform-specific checks
    if platform.system() == 'Windows':
        try:
            import ctypes
        except ImportError:
            missing.append("ctypes")
    elif platform.system() == 'Darwin':
        try:
            from Quartz import CGDisplayBounds
        except ImportError:
            missing.append("pyobjc-framework-Quartz")
    
    if missing:
        print(f"Warning: Missing dependencies: {', '.join(missing)}")
        print("Some features may not work correctly.")
        return False
    return True

# Helper function to find primary monitor
def get_primary_monitor(sct):
    try:
        # Try to find the primary monitor
        if platform.system() == 'Windows':
            # On Windows, try to use Win32 API to find primary
            try:
                primary_index = 0
                for i, monitor in enumerate(sct.monitors[1:], 1):
                    if monitor.get("left") == 0 and monitor.get("top") == 0:
                        primary_index = i
                        break
                return sct.monitors[primary_index]
            except Exception:
                return sct.monitors[1]  # Fallback to default
        elif platform.system() == 'Linux':
            # Try to find primary monitor on Linux
            for i, monitor in enumerate(sct.monitors[1:], 1):
                if monitor.get("left") == 0 and monitor.get("top") == 0:
                    return sct.monitors[i]
            return sct.monitors[1]  # Fallback to default
        elif platform.system() == 'Darwin':
            return sct.monitors[0]  # On macOS, monitor 0 is the primary display
        else:
            return sct.monitors[0]  # Default for other platforms
    except Exception:
        # Fallback to first monitor
        return sct.monitors[0]

# Capture screen with region option for better performance
def capture_screen(region=None):
    try:
        with mss.mss() as sct:
            if region:
                # Ensure region values are valid
                region = [max(0, region[0]), max(0, region[1]), 
                         max(1, region[2]), max(1, region[3])]
                # Ensure width and height are positive integers
                if region[2] <= 0 or region[3] <= 0:
                    # Invalid region, fall back to full screen
                    primary_monitor = get_primary_monitor(sct)
                    screen = sct.grab(primary_monitor)
                else:
                    monitor = {"top": region[1], "left": region[0], 
                              "width": region[2], "height": region[3]}
                    screen = sct.grab(monitor)
            else:
                # Get the primary monitor using the helper function
                primary_monitor = get_primary_monitor(sct)
                screen = sct.grab(primary_monitor)
                
                # Store if this is a Retina display for later use (macOS only)
                global is_retina_display
                is_retina_display = False
                if platform.system() == 'Darwin' and hasattr(screen, 'width') and screen.width > 0:
                    screen_width = pyautogui.size()[0]
                    if screen.width > screen_width * 1.5:  # Likely a Retina display
                        is_retina_display = True
                
            img = np.array(screen)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            img = cv2.GaussianBlur(img, (5, 5), 0)
            return img
    except Exception as e:
        print(f"Screen capture error: {e}")
        # Return a small black image as fallback
        return np.zeros((100, 100, 3), dtype=np.uint8)

# Find target using color detection
# Global variable to track if we're on a Retina display
is_retina_display = False

def find_target(img):
    try:
        # Check if image is valid
        if img is None or img.size == 0 or len(img.shape) < 3:
            print("Invalid image for target detection")
            return None
            
        screen_width, screen_height = pyautogui.size()
        img_height, img_width, _ = img.shape
        
        # Enhanced preprocessing for better detection
        # Apply contrast enhancement
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        enhanced_lab = cv2.merge((cl, a, b))
        img = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # Create mask from multiple color ranges
        combined_mask = np.zeros(img.shape[:2], dtype=np.uint8)
        
        for color in TARGET_COLORS:
            lower = np.array([max(0, c - COLOR_TOLERANCE) for c in color], dtype=np.uint8)
            upper = np.array([min(255, c + COLOR_TOLERANCE) for c in color], dtype=np.uint8)
            color_mask = cv2.inRange(img, lower, upper)
            combined_mask = cv2.bitwise_or(combined_mask, color_mask)
        
        # Advanced mask processing
        mask = cv2.erode(combined_mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=4)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
            
        # Filter and find largest contour
        valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > MIN_CONTOUR_AREA]
        if not valid_contours:
            return None
            
        largest = max(valid_contours, key=cv2.contourArea)
        
        # Get target position
        M = cv2.moments(largest)
        if M["m00"] == 0:
            return None
            
        # Get bounding rectangle for headshot targeting
        x, y, w, h = cv2.boundingRect(largest)
        
        # Target the center of the top portion of the contour (more precise headshot)
        target_x = M["m10"] / M["m00"]  # Center X position
        target_y = y + h * HEADSHOT_PERCENTAGE  # Target upper portion for better precision (headshot)
        
        # Convert to screen coordinates
        target_x = target_x * screen_width / img_width
        target_y = target_y * screen_height / img_height
        
        # Apply Retina display scaling correction if needed
        if platform.system() == 'Darwin' and is_retina_display:
            # On Retina displays, we need to divide by 2 to get the correct screen position
            target_x /= 2
            target_y /= 2
            
            # Also adjust the bounding box for consistent region tracking
            x /= 2
            y /= 2
            w /= 2
            h /= 2
            
        return (target_x, target_y, (x, y, w, h))
    except Exception as e:
        print(f"Target detection error: {e}")
        return None

# Aim at target with platform-specific optimizations
def aim_at_target(x, y):
    try:
        screen_width, screen_height = pyautogui.size()
        
        # Ensure coordinates are within screen bounds and are valid numbers
        if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
            print("Invalid target coordinates")
            return False
            
        if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
            print("Invalid target coordinates (NaN or Inf)")
            return False
        
        # Use exact floating point values for more precise positioning
        # This avoids rounding errors that can reduce accuracy
        x = float(x)
        y = float(y)
        
        # Ensure coordinates are within screen bounds
        x = max(0, min(x, screen_width - 1))
        y = max(0, min(y, screen_height - 1))
        
        # Platform-specific mouse movement
        if platform.system() == 'Windows':
            try:
                # Use direct Win32 API for more accurate mouse movement on Windows
                x_int, y_int = int(round(x)), int(round(y))
                ctypes.windll.user32.SetCursorPos(x_int, y_int)
                
                # Add stabilization pause for first shot accuracy
                time.sleep(0.05)
                
                # Double-check position with a second call for accuracy
                ctypes.windll.user32.SetCursorPos(x_int, y_int)
            except Exception:
                # Fall back to pyautogui if Win32 API fails
                pyautogui.moveTo(x, y, duration=0)
                time.sleep(0.05)  # Stabilization pause
        elif platform.system() == 'Darwin':  # macOS
            try:
                # For macOS, use Quartz for more accurate positioning
                main_display = CGMainDisplayID()
                main_height = CGDisplayPixelsHigh(main_display)
                
                # Convert to Quartz coordinate system (origin at bottom left)
                quartz_y = main_height - y
                
                # Use Quartz for mouse movement with stabilization
                quartz_x = float(x)
                quartz_y = float(quartz_y)
                CGPostMouseEvent((quartz_x, quartz_y), True, 1, False)
                
                # Add stabilization pause for first shot accuracy
                time.sleep(0.05)
                
                # Verify position with a second call
                CGPostMouseEvent((quartz_x, quartz_y), True, 1, False)
            except Exception as e:
                # Fall back to pyautogui if Quartz fails
                print(f"Quartz mouse movement failed: {e}, falling back to pyautogui")
                pyautogui.moveTo(x, y, duration=0)
                time.sleep(0.05)  # Stabilization pause
        else:
            # For Linux, use pyautogui with stabilization
            pyautogui.moveTo(int(round(x)), int(round(y)), duration=0)
            time.sleep(0.05)  # Stabilization pause
            pyautogui.moveTo(int(round(x)), int(round(y)), duration=0)  # Verify position
        
        return True
    except Exception as e:
        print(f"Aiming error: {e}")
        return False

# Global variables for key states
key_states = {
    SCAN_KEY: False,
    AIM_KEY: False,
    EXIT_KEY: False,
    SAVE_CONFIG_KEY: False,
    LOAD_CONFIG_KEY: False
}
last_key_time = {
    SCAN_KEY: 0,
    AIM_KEY: 0,
    EXIT_KEY: 0,
    SAVE_CONFIG_KEY: 0,
    LOAD_CONFIG_KEY: 0
}
# Track which keys should actually trigger actions
action_keys = [SCAN_KEY, AIM_KEY, EXIT_KEY, SAVE_CONFIG_KEY, LOAD_CONFIG_KEY]
key_lock = threading.Lock()

# Keyboard listener setup
def on_press(key):
    try:
        k = key.char.lower() if hasattr(key, 'char') and key.char is not None else None
        if k is None:
            return
            
        current_time = time.time()
        with key_lock:
            if k in key_states:
                # Only process keys that should trigger actions
                if k in action_keys:
                    # For AIM_KEY, we only want a single press event, not continuous
                    if k == AIM_KEY:
                        # Only register if it wasn't already pressed and enough time has passed
                        if not key_states[k] and current_time - last_key_time[k] > 0.5:
                            key_states[k] = True
                            last_key_time[k] = current_time
                    # For other action keys, prevent key repeat issues with a smaller delay
                    elif current_time - last_key_time[k] > 0.3 or k == EXIT_KEY:
                        key_states[k] = True
                        last_key_time[k] = current_time
                # For WASD keys, we don't need to do anything - just ignore them
                # This prevents them from triggering any actions
    except (TypeError, AttributeError):
        # Handle TypeError (can't convert to lower) or AttributeError (NoneType has no attribute 'lower')
        pass

def on_release(key):
    try:
        k = key.char.lower() if hasattr(key, 'char') and key.char is not None else None
        if k is None:
            return
            
        with key_lock:
            if k in key_states:
                key_states[k] = False
    except (TypeError, AttributeError):
        # Handle TypeError (can't convert to lower) or AttributeError (NoneType has no attribute 'lower')
        pass

# Start keyboard listener
keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
# Don't start it here, we'll start it in the main function

# Check if key is pressed
def key_pressed():
    with key_lock:
        # Only check keys that should trigger actions
        if key_states[EXIT_KEY]:
            return EXIT_KEY
        elif key_states[SCAN_KEY]:
            key_states[SCAN_KEY] = False  # Reset after reading
            return SCAN_KEY
        elif key_states[AIM_KEY]:
            key_states[AIM_KEY] = False  # Reset immediately after reading
            # Also reset the last key time to prevent immediate re-triggering
            last_key_time[AIM_KEY] = time.time()
            return AIM_KEY
        elif key_states[SAVE_CONFIG_KEY]:
            key_states[SAVE_CONFIG_KEY] = False  # Reset after reading
            return SAVE_CONFIG_KEY
        elif key_states[LOAD_CONFIG_KEY]:
            key_states[LOAD_CONFIG_KEY] = False  # Reset after reading
            return LOAD_CONFIG_KEY
    return None

# Function to update configuration from current settings
def update_config_from_current():
    global CONFIG
    CONFIG['color_tolerance'] = COLOR_TOLERANCE
    CONFIG['min_contour_area'] = MIN_CONTOUR_AREA
    CONFIG['scan_key'] = SCAN_KEY
    CONFIG['aim_key'] = AIM_KEY
    CONFIG['exit_key'] = EXIT_KEY
    CONFIG['save_config_key'] = SAVE_CONFIG_KEY
    CONFIG['load_config_key'] = LOAD_CONFIG_KEY
    CONFIG['headshot_percentage'] = HEADSHOT_PERCENTAGE
    # Convert tuples to lists for JSON serialization
    CONFIG['target_colors'] = [list(color) for color in TARGET_COLORS]
    return CONFIG

# Function to update current settings from configuration
def update_current_from_config():
    global TARGET_COLORS, COLOR_TOLERANCE, MIN_CONTOUR_AREA
    global SCAN_KEY, AIM_KEY, EXIT_KEY, SAVE_CONFIG_KEY, LOAD_CONFIG_KEY, HEADSHOT_PERCENTAGE
    global key_states, last_key_time, action_keys
    
    # Update all settings from CONFIG
    TARGET_COLORS = [tuple(color) for color in CONFIG['target_colors']]
    COLOR_TOLERANCE = CONFIG['color_tolerance']
    MIN_CONTOUR_AREA = CONFIG['min_contour_area']
    SCAN_KEY = CONFIG['scan_key']
    AIM_KEY = CONFIG['aim_key']
    EXIT_KEY = CONFIG['exit_key']
    SAVE_CONFIG_KEY = CONFIG['save_config_key']
    LOAD_CONFIG_KEY = CONFIG['load_config_key']
    HEADSHOT_PERCENTAGE = CONFIG['headshot_percentage']
    
    # Update key tracking
    key_states = {
        SCAN_KEY: False,
        AIM_KEY: False,
        EXIT_KEY: False,
        SAVE_CONFIG_KEY: False,
        LOAD_CONFIG_KEY: False
    }
    last_key_time = {
        SCAN_KEY: 0,
        AIM_KEY: 0,
        EXIT_KEY: 0,
        SAVE_CONFIG_KEY: 0,
        LOAD_CONFIG_KEY: 0
    }
    action_keys = [SCAN_KEY, AIM_KEY, EXIT_KEY, SAVE_CONFIG_KEY, LOAD_CONFIG_KEY]
    
    # Print the updated configuration
    config.print_config(CONFIG)

# Function to reload configuration
def reload_config():
    global CONFIG
    CONFIG = config.load_config()
    update_current_from_config()

# Main aimbot function
def aimbot():
    print("Aimbot started!")
    print(f"Running on {platform.system()}")
    print(f"Press '{SCAN_KEY}' to toggle continuous scanning on/off")
    print(f"Press '{SAVE_CONFIG_KEY}' to save current configuration")
    print(f"Press '{LOAD_CONFIG_KEY}' to reload configuration")
    print(f"Press '{EXIT_KEY}' to exit")
    
    # Print current configuration
    config.print_config(CONFIG)
    
    last_region = None
    current_target = None
    running = True
    scanning_active = False
    scan_count = 0
    
    while running:
        # Check for input (non-blocking)
        key = key_pressed()
        
        if key == EXIT_KEY:
            running = False
            print("Exiting...")
            break
            
        # Toggle scanning on/off
        if key == SCAN_KEY:
            scanning_active = not scanning_active
            if scanning_active:
                print("Continuous scanning activated")
            else:
                print("Scanning stopped")
        
        # Save current configuration
        if key == SAVE_CONFIG_KEY:
            print("Saving current configuration...")
            updated_config = update_config_from_current()
            if config.save_config(updated_config):
                print("Configuration saved successfully!")
            else:
                print("Failed to save configuration.")
        
        # Reload configuration
        if key == LOAD_CONFIG_KEY:
            print("Reloading configuration...")
            reload_config()
            print("Configuration reloaded!")
        
        # Scan if scanning is active
        if scanning_active:
            scan_count += 1
            
            # Use region-based capture if we have a previous target
            screen = capture_screen(last_region) if last_region else capture_screen()
            
            target_info = find_target(screen)
            
            if target_info:
                x, y, bbox = target_info
                print(f"Target found at ({int(x)}, {int(y)})")
                current_target = (x, y)
                
                # Update region for next scan (with padding)
                padding = 100
                x1, y1, w, h = bbox
                if last_region:
                    # Adjust bbox coordinates to screen coordinates
                    x1 += last_region[0]
                    y1 += last_region[1]
                
                # Apply Retina display scaling for region if needed
                if platform.system() == 'Darwin' and is_retina_display:
                    # For Retina displays, apply consistent scaling
                    scale_factor = 2  # Always use scale factor of 2 for Retina displays
                    padding *= scale_factor
                    w *= scale_factor
                    h *= scale_factor
                
                # Create region with padding
                last_region = (
                    max(0, int(x1 - padding)),
                    max(0, int(y1 - padding)),
                    max(1, int(w + padding * 2)),
                    max(1, int(h + padding * 2))
                )
                
                # Don't automatically aim at targets when found
                # Only store the target position for manual aiming with AIM_KEY
                
                # Small pause for system stability
                time.sleep(0.02)  # Reduced delay for faster response
            else:
                # If no target found in region, try full screen next time
                last_region = None
                current_target = None
                
                # Small pause to prevent CPU overload
                time.sleep(0.05)
        
        # Aim at target if AIM_KEY is pressed and we have a target
        if key == AIM_KEY and current_target:
            x, y = current_target
            print(f"Aiming at ({int(x)}, {int(y)})")
            aim_at_target(x, y)
        
        # Small pause for system stability
        time.sleep(0.01)

# Main function
def main():
    global CONFIG
    # Check dependencies
    if not check_dependencies():
        print("Warning: Some dependencies are missing. The program may not work correctly.")
        choice = input("Continue anyway? (y/n): ")
        if choice.lower() != 'y':
            sys.exit(1)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--config':
            # Run configuration menu
            print("Opening configuration menu...")
            while True:
                config.print_config(CONFIG)
                CONFIG = config.modify_config(CONFIG)
                save = input("Save changes? (y/n): ")
                if save.lower() == 'y':
                    if config.save_config(CONFIG):
                        print("Configuration saved!")
                    else:
                        print("Failed to save configuration.")
                
                again = input("Continue editing? (y/n): ")
                if again.lower() != 'y':
                    break
            
            # Update current settings from the modified config
            update_current_from_config()
    
    # Start keyboard listener
    keyboard_listener.start()
    
    try:
        # Run aimbot
        aimbot()
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Stop keyboard listener
        keyboard_listener.stop()
        keyboard_listener.join()
        print("Program terminated.")

if __name__ == "__main__":
    main()
