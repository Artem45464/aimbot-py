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
AIM_DELAY = CONFIG.get('aim_delay', 0.0)  # Default to 0 if not in config
AUTO_FIRE = CONFIG.get('auto_fire', False)  # Default to False if not in config
DYNAMIC_AREA = CONFIG.get('dynamic_area', True)  # Default to True if not in config

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
# Global variables
is_retina_display = False
previous_targets = []
last_aim_time = 0
target_velocity_history = []
accuracy_stats = {'hits': 0, 'misses': 0}

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
        
        # Determine minimum contour area based on dynamic adjustment
        min_area = MIN_CONTOUR_AREA
        if DYNAMIC_AREA:
            # If we're looking at a small region, reduce the minimum area
            # This helps detect targets that are far away (smaller on screen)
            if img_width < screen_width / 2 or img_height < screen_height / 2:
                # Calculate a scaling factor based on how small the region is
                scale_factor = (img_width * img_height) / (screen_width * screen_height)
                # More aggressive scaling for distant targets (smaller minimum area)
                min_area = max(3, int(MIN_CONTOUR_AREA * scale_factor))
                
        # Filter and find largest contour
        valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
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
        
        # Advanced adaptive headshot targeting based on target size and movement
        adjusted_headshot = HEADSHOT_PERCENTAGE
        contour_area = cv2.contourArea(largest)
        
        # For small/distant targets, aim higher
        if contour_area < MIN_CONTOUR_AREA * 3:
            adjusted_headshot = max(0.05, HEADSHOT_PERCENTAGE - 0.05)  # Aim higher
        
        # Check if target is moving (if we have previous targets)
        if len(previous_targets) >= 2:
            # Calculate vertical velocity if we have previous targets
            try:
                current_time = time.time()  # Get current time
                prev_x, prev_y = previous_targets[-1][0], previous_targets[-1][1]
                time_diff = current_time - previous_targets[-1][2]
                
                if time_diff > 0:
                    # If target is moving upward, aim slightly higher to compensate
                    y_velocity = (y - prev_y) / time_diff
                    if y_velocity < -5:  # Moving up
                        adjusted_headshot = max(0.03, adjusted_headshot - 0.03)
                    # If target is moving downward, aim slightly lower to compensate
                    elif y_velocity > 5:  # Moving down
                        adjusted_headshot = min(0.15, adjusted_headshot + 0.03)
            except (IndexError, KeyError):
                pass  # Ignore if we can't calculate velocity
            
        target_y = y + h * adjusted_headshot  # Target upper portion for better precision (headshot)
        
        # Convert to screen coordinates
        target_x = target_x * screen_width / img_width
        target_y = target_y * screen_height / img_height
        
        # Apply Retina display scaling correction if needed
        if platform.system() == 'Darwin' and is_retina_display:
            # On Retina displays, we need to divide by 2 to get the correct screen position
            target_x /= 2
            target_y /= 2
            
        return (target_x, target_y, (x, y, w, h))
    except Exception as e:
        print(f"Target detection error: {e}")
        return None

# These variables are already defined at the top of the file

# Aim at target with adaptive intelligence
def aim_at_target(x, y):
    try:
        global previous_targets, last_aim_time
        screen_width, screen_height = pyautogui.size()
        current_time = time.time()
        
        # Validate coordinates
        if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
            print("Invalid target coordinates")
            return False
            
        if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
            print("Invalid target coordinates (NaN or Inf)")
            return False
        
        # Store target for movement prediction
        previous_targets.append((x, y, current_time))
        # Keep only recent targets (last 5)
        if len(previous_targets) > 5:
            previous_targets.pop(0)
            
        # Predict target movement if we have enough data
        predicted_x, predicted_y = x, y
        if len(previous_targets) >= 3:
            # Calculate velocity based on previous positions with weighted average
            time_diff = previous_targets[-1][2] - previous_targets[-3][2]
            if time_diff > 0:
                x_velocity = (previous_targets[-1][0] - previous_targets[-3][0]) / time_diff
                y_velocity = (previous_targets[-1][1] - previous_targets[-3][1]) / time_diff
                
                # Store velocity data for adaptive learning
                target_velocity_history.append((x_velocity, y_velocity))
                if len(target_velocity_history) > 10:
                    target_velocity_history.pop(0)
                
                # Use weighted average of recent velocities for more stable prediction
                if len(target_velocity_history) >= 3:
                    weights = [0.5, 0.3, 0.2]  # Most recent velocities have higher weight
                    x_velocity_avg = sum(v[0] * w for v, w in zip(target_velocity_history[-3:], weights))
                    y_velocity_avg = sum(v[1] * w for v, w in zip(target_velocity_history[-3:], weights))
                    
                    # Apply acceleration factor if target is accelerating
                    if len(target_velocity_history) >= 5:
                        x_accel = (target_velocity_history[-1][0] - target_velocity_history[-5][0]) / 4
                        y_accel = (target_velocity_history[-1][1] - target_velocity_history[-5][1]) / 4
                        
                        # Get acceleration compensation from config (0-100%)
                        accel_compensation = CONFIG.get('accel_compensation', 50) / 100.0
                        x_velocity_avg += x_accel * accel_compensation
                        y_velocity_avg += y_accel * accel_compensation
                        
                        # Apply learning from accuracy stats
                        if accuracy_stats['hits'] + accuracy_stats['misses'] > 10:
                            hit_rate = accuracy_stats['hits'] / (accuracy_stats['hits'] + accuracy_stats['misses'])
                            # Adjust prediction based on hit rate
                            if hit_rate < 0.5:  # If accuracy is low, be more aggressive with prediction
                                x_velocity_avg *= 1.2
                                y_velocity_avg *= 1.2
                            elif hit_rate > 0.8:  # If accuracy is high, be more conservative
                                x_velocity_avg *= 0.9
                                y_velocity_avg *= 0.9
                            hit_rate = accuracy_stats['hits'] / (accuracy_stats['hits'] + accuracy_stats['misses'])
                            # Adjust prediction based on hit rate
                            if hit_rate < 0.5:  # If accuracy is low, be more aggressive with prediction
                                x_velocity_avg *= 1.2
                                y_velocity_avg *= 1.2
                    
                    # Predict position based on aim delay and system latency
                    # Get latency compensation from config (0-100ms)
                    latency_ms = CONFIG.get('latency_compensation', 50) / 1000.0  # Convert to seconds
                    system_latency = latency_ms  # Use configured latency
                    
                    # Get current position for distance calculation
                    current_x, current_y = pyautogui.position()
                    # Calculate distance for adaptive latency
                    target_distance = math.sqrt((x - current_x)**2 + (y - current_y)**2)
                    
                    # Add extra latency for long distances
                    if target_distance > 300:
                        system_latency += 0.01  # Add 10ms for long distances
                    
                    prediction_time = AIM_DELAY + system_latency
                    predicted_x = x + (x_velocity_avg * prediction_time)
                    predicted_y = y + (y_velocity_avg * prediction_time)
                else:
                    # Simple prediction if not enough velocity history
                    prediction_time = AIM_DELAY + 0.05
                    predicted_x = x + (x_velocity * prediction_time)
                    predicted_y = y + (y_velocity * prediction_time)
                
                # Ensure predicted position is within screen bounds
                predicted_x = max(0, min(predicted_x, screen_width - 1))
                predicted_y = max(0, min(predicted_y, screen_height - 1))
        
        # Use exact floating point values
        x = float(predicted_x)
        y = float(predicted_y)
        
        # Get current position
        current_x, current_y = pyautogui.position()
        
        # Calculate distance and adapt movement strategy
        distance = math.sqrt((x - current_x)**2 + (y - current_y)**2)
        
        # Adaptive movement based on distance
        if platform.system() == 'Windows':
            try:
                x_int, y_int = int(round(x)), int(round(y))
                
                # Adapt steps based on distance
                steps = 1
                if distance > 300:
                    steps = 5
                elif distance > 100:
                    steps = 3
                
                # Use bezier curve for more natural, human-like movement
                if steps > 1:
                    # Calculate control point for bezier curve (slight arc toward target)
                    control_x = current_x + (x_int - current_x) * 0.5 + (y_int - current_y) * 0.1
                    control_y = current_y + (y_int - current_y) * 0.5 - (x_int - current_x) * 0.1
                    
                    # Move along bezier curve for more natural movement
                    for i in range(1, steps):
                        t = i / steps
                        # Quadratic bezier formula: B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
                        t_inv = 1.0 - t
                        bezier_x = t_inv*t_inv*current_x + 2*t_inv*t*control_x + t*t*x_int
                        bezier_y = t_inv*t_inv*current_y + 2*t_inv*t*control_y + t*t*y_int
                        ctypes.windll.user32.SetCursorPos(int(bezier_x), int(bezier_y))
                        # Dynamic timing based on distance to target
                        time.sleep(0.003 + (0.007 * (1 - i/steps)))
                
                # Final precise movement
                ctypes.windll.user32.SetCursorPos(x_int, y_int)
                
                # Adaptive stabilization based on distance
                stabilize_time = min(0.1, max(0.02, distance / 2000))
                time.sleep(stabilize_time)
                
                # Verify position
                ctypes.windll.user32.SetCursorPos(x_int, y_int)
            except Exception:
                pyautogui.moveTo(x, y, duration=min(0.1, max(0.01, distance / 2000)))
                time.sleep(0.05)
        
        elif platform.system() == 'Darwin':
            try:
                main_display = CGMainDisplayID()
                main_height = CGDisplayPixelsHigh(main_display)
                
                # Convert to Quartz coordinates
                quartz_y = main_height - y
                quartz_x = float(x)
                
                # Adapt steps based on distance
                steps = 1
                if distance > 300:
                    steps = 5
                elif distance > 100:
                    steps = 3
                
                # Use bezier curve for more natural, human-like movement on macOS
                if steps > 1:
                    # Calculate control point for bezier curve (slight arc toward target)
                    control_x = current_x + (quartz_x - current_x) * 0.5 + (quartz_y - (main_height - current_y)) * 0.1
                    control_y = (main_height - current_y) + (quartz_y - (main_height - current_y)) * 0.5 - (quartz_x - current_x) * 0.1
                    
                    # Move along bezier curve for more natural movement
                    for i in range(1, steps):
                        t = i / steps
                        # Quadratic bezier formula: B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
                        t_inv = 1.0 - t
                        bezier_x = t_inv*t_inv*current_x + 2*t_inv*t*control_x + t*t*quartz_x
                        bezier_y = t_inv*t_inv*(main_height - current_y) + 2*t_inv*t*control_y + t*t*quartz_y
                        CGPostMouseEvent((bezier_x, bezier_y), True, 1, False)
                        # Dynamic timing based on distance to target
                        time.sleep(0.003 + (0.007 * (1 - i/steps)))
                
                # Final precise movement
                CGPostMouseEvent((quartz_x, quartz_y), True, 1, False)
                
                # Adaptive stabilization based on distance
                stabilize_time = min(0.1, max(0.02, distance / 2000))
                time.sleep(stabilize_time)
                
                # Verify position
                CGPostMouseEvent((quartz_x, quartz_y), True, 1, False)
            except Exception as e:
                print(f"Quartz mouse movement failed: {e}, falling back to pyautogui")
                pyautogui.moveTo(x, y, duration=min(0.1, max(0.01, distance / 2000)))
                time.sleep(0.05)
        
        else:  # Linux
            # Adapt steps based on distance
            steps = 1
            if distance > 300:
                steps = 5
            elif distance > 100:
                steps = 3
            
            # Use bezier curve for more natural, human-like movement on Linux
            if steps > 1:
                # Calculate control point for bezier curve (slight arc toward target)
                control_x = current_x + (x - current_x) * 0.5 + (y - current_y) * 0.1
                control_y = current_y + (y - current_y) * 0.5 - (x - current_x) * 0.1
                
                # Move along bezier curve for more natural movement
                for i in range(1, steps):
                    t = i / steps
                    # Quadratic bezier formula: B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
                    t_inv = 1.0 - t
                    bezier_x = t_inv*t_inv*current_x + 2*t_inv*t*control_x + t*t*x
                    bezier_y = t_inv*t_inv*current_y + 2*t_inv*t*control_y + t*t*y
                    pyautogui.moveTo(int(round(bezier_x)), int(round(bezier_y)), duration=0.003 + (0.007 * (1 - i/steps)))
            
            # Final precise movement
            pyautogui.moveTo(int(round(x)), int(round(y)), duration=0.01)
            
            # Adaptive stabilization based on distance
            stabilize_time = min(0.1, max(0.02, distance / 2000))
            time.sleep(stabilize_time)
        
        # Update last aim time
        last_aim_time = current_time
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
    CONFIG['aim_delay'] = AIM_DELAY
    CONFIG['auto_fire'] = AUTO_FIRE
    CONFIG['dynamic_area'] = DYNAMIC_AREA
    
    # Save advanced targeting settings
    if 'prediction_strength' not in CONFIG:
        CONFIG['prediction_strength'] = 100
    if 'accel_compensation' not in CONFIG:
        CONFIG['accel_compensation'] = 50
    if 'latency_compensation' not in CONFIG:
        CONFIG['latency_compensation'] = 50
        
    # Convert tuples to lists for JSON serialization
    CONFIG['target_colors'] = [list(color) for color in TARGET_COLORS]
    return CONFIG

# Function to update current settings from configuration
def update_current_from_config():
    global TARGET_COLORS, COLOR_TOLERANCE, MIN_CONTOUR_AREA
    global SCAN_KEY, AIM_KEY, EXIT_KEY, SAVE_CONFIG_KEY, LOAD_CONFIG_KEY, HEADSHOT_PERCENTAGE, AIM_DELAY, AUTO_FIRE, DYNAMIC_AREA
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
    AIM_DELAY = CONFIG.get('aim_delay', 0.0)  # Default to 0 if not in config
    AUTO_FIRE = CONFIG.get('auto_fire', False)  # Default to False if not in config
    DYNAMIC_AREA = CONFIG.get('dynamic_area', True)  # Default to True if not in config
    
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
    print(f"Press '{AIM_KEY}' to aim at the last found target")
    print(f"Press '{SAVE_CONFIG_KEY}' to save current configuration")
    print(f"Press '{LOAD_CONFIG_KEY}' to reload configuration")
    print(f"Press '{EXIT_KEY}' to exit")
    
    # Show auto fire status
    if AUTO_FIRE:
        print("Auto fire is ENABLED - will automatically click when aiming")
    
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
                    # Scale all coordinates for proper region tracking
                    x1 *= scale_factor
                    y1 *= scale_factor
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
        if key == AIM_KEY:
            if current_target:
                x, y = current_target
                print(f"Aiming at ({int(x)}, {int(y)})")
                
                # Apply aim delay if configured
                if AIM_DELAY > 0:
                    print(f"Applying aim delay of {AIM_DELAY} seconds...")
                    time.sleep(AIM_DELAY)
                    
                aim_at_target(x, y)
                
                # Auto fire if enabled
                if AUTO_FIRE:
                    print("Auto firing...")
                    pyautogui.click()
                    
                    # Track accuracy for learning
                    # We assume a hit if we're still on target after a short delay
                    def check_hit():
                        time.sleep(0.3)  # Wait to see if target is still there
                        if scanning_active:
                            screen = capture_screen(last_region) if last_region else capture_screen()
                            if find_target(screen):
                                accuracy_stats['misses'] += 1
                            else:
                                accuracy_stats['hits'] += 1
                            print(f"Accuracy: {accuracy_stats['hits']}/{accuracy_stats['hits'] + accuracy_stats['misses']} " + 
                                  f"({int(accuracy_stats['hits'] * 100 / (accuracy_stats['hits'] + accuracy_stats['misses']))}%)")
                    
                    # Start hit detection in a separate thread
                    threading.Thread(target=check_hit, daemon=True).start()
            else:
                print("No target found. Scan for targets first.")
        
        # Small pause for system stability
        time.sleep(0.01)

# Main function
def main():
    global CONFIG
    # Check if aim_delay is in the config, add it if not
    if 'aim_delay' not in CONFIG:
        CONFIG['aim_delay'] = 0.0
        config.save_config(CONFIG)
        
    # Check if auto_fire is in the config, add it if not
    if 'auto_fire' not in CONFIG:
        CONFIG['auto_fire'] = False
        config.save_config(CONFIG)
        
    # Check if dynamic_area is in the config, add it if not
    if 'dynamic_area' not in CONFIG:
        CONFIG['dynamic_area'] = True
        config.save_config(CONFIG)
        
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
