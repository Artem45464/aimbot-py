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
from pynput import keyboard

# Configuration
TARGET_COLORS = [
    (255, 0, 0),    # Red
    (240, 10, 10),  # Slightly different red
    (220, 0, 0)     # Darker red
]
COLOR_TOLERANCE = 75
MIN_CONTOUR_AREA = 20
SCAN_KEY = 'y'      # Key to toggle scanning on/off
AIM_KEY = 'f'       # Key to aim at the last found target (changed from 'a' to avoid WASD conflicts)
EXIT_KEY = 'q'      # Key to exit

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
                import ctypes
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
        
        # Create mask from multiple color ranges
        combined_mask = np.zeros(img.shape[:2], dtype=np.uint8)
        
        for color in TARGET_COLORS:
            lower = np.array([max(0, c - COLOR_TOLERANCE) for c in color], dtype=np.uint8)
            upper = np.array([min(255, c + COLOR_TOLERANCE) for c in color], dtype=np.uint8)
            color_mask = cv2.inRange(img, lower, upper)
            combined_mask = cv2.bitwise_or(combined_mask, color_mask)
        
        # Process mask
        mask = cv2.erode(combined_mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=4)
    except Exception as e:
        print(f"Error in image processing: {e}")
        return None

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
    
    # Target the top 20% of the contour (headshot)
    target_x = M["m10"] / M["m00"]
    target_y = y + h * 0.2  # Target upper portion
    
    # Convert to screen coordinates
    target_x = target_x * screen_width / img_width
    target_y = target_y * screen_height / img_height
    
    # Apply Retina display scaling correction if needed
    if platform.system() == 'Darwin' and is_retina_display:
        # On Retina displays, we need to divide by 2 to get the correct screen position
        target_x /= 2
        target_y /= 2
    
    return target_x, target_y, (x, y, w, h)  # Return target coords and bounding box

# Move mouse to target (no click)
def aim_at_target(target_pos):
    if not target_pos:
        return False
    
    try:
        x, y = float(target_pos[0]), float(target_pos[1])
        screen_width, screen_height = pyautogui.size()
        
        # Ensure coordinates are within screen bounds and are valid numbers
        if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
            print("Invalid target coordinates")
            return False
            
        if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
            print("Invalid target coordinates (NaN or Inf)")
            return False
            
        x = max(0, min(x, screen_width))
        y = max(0, min(y, screen_height))
        
        # Platform-specific mouse movement
        if platform.system() == 'Windows':
            try:
                # Use direct Win32 API for more accurate mouse movement on Windows
                import ctypes
                ctypes.windll.user32.SetCursorPos(int(x), int(y))
            except Exception:
                # Fall back to pyautogui if Win32 A                # Fall back to pyautogui if Win32 A                # Fall back to pyautogui if Win32 API fails
                pyautogui.moveTo(x, y, duration=0.01)
        elif platform.system() == 'Darwin':  # macOS
            try:
                # For macOS, use Quartz for more accurate positioning
                from Quartz import CGDisplayBounds, CGMainDisplayID, CGPostMouseEvent, CGDisplayPixelsHigh
                
                # Get the main display
                main_display = CGMainDisplayID()
                main_height = CGDisplayPixelsHigh(main_display)
                
                # Convert to Quartz coordinate system (origin at bottom left)
                quartz_y = main_height - y
                
                # Use Quartz for mouse movement
                CGPostMouseEvent((x, quartz_y), True, 1, False)
            except Exception as e:
                # Fall back to pyautogui if Quartz fails
                print(f"Quartz mouse movement failed: {e}, falling back to pyautogui")
                pyautogui.moveTo(x, y, duration=0.005)
        else:
            # Use default duration for Linux
            pyautogui.moveTo(x, y, duration=0.01)
        return True
    except Exception as e:
        print(f"Aiming error: {e}")
        return False

# Global variables for key states
key_states = {
    SCAN_KEY: False,
    AIM_KEY: False,
    EXIT_KEY: False,
    # Add WASD keys to prevent them from interfering
    'w': False,
    'a': False,
    's': False,
    'd': False
}
last_key_time = {
    SCAN_KEY: 0,
    AIM_KEY: 0,
    EXIT_KEY: 0,
    'w': 0,
    'a': 0,
    's': 0,
    'd': 0
}
# Track which keys should actually trigger actions
action_keys = [SCAN_KEY, AIM_KEY, EXIT_KEY]
key_lock = threading.Lock()

# Keyboard listener setup
def on_press(key):
    try:
        k = key.char.lower()
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
                else:
                    # For non-action keys like WASD, just track their state but don't trigger actions
                    key_states[k] = True
                    last_key_time[k] = current_time
    except (AttributeError, TypeError):
        # Handle both AttributeError (no char attribute) and TypeError (can't convert to lower)
        pass

def on_release(key):
    try:
        k = key.char.lower()
        with key_lock:
            if k in key_states:
                key_states[k] = False
    except (AttributeError, TypeError):
        # Handle both AttributeError (no char attribute) and TypeError (can't convert to lower)
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
    return None

# Main aimbot function
def aimbot():
    print("Aimbot started!")
    print(f"Running on {platform.system()}")
    print(f"Press '{SCAN_KEY}' to toggle continuous scanning on/off")
    print(f"Press '{AIM_KEY}' to aim at the last found target")
    print(f"Press '{EXIT_KEY}' to exit")
    
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
                    scale_factor = 2 if not last_region else 1
                    padding *= scale_factor
                    w *= scale_factor
                    h *= scale_factor
                
                # Create region with padding
                last_region = (
                    max(0, x1 - padding),
                    max(0, y1 - padding),
                    w + padding * 2,
                    h + padding * 2
                )
                
                # Auto-aim at target when found
                aim_at_target(current_target)
                print("Aimed at target")
                
                # Brief pause after finding a target
                time.sleep(0.2)
            else:
                # Only print "scanning" message occasionally to avoid spam
                if scan_count % 20 == 0:
                    print("Scanning...")
                    scan_count = 0
        
        # Aim at target when aim key is pressed
        if key == AIM_KEY and current_target:
            print(f"Aiming at target ({int(current_target[0])}, {int(current_target[1])})")
            aim_at_target(current_target)
            # Add a small delay to prevent multiple rapid movements
            time.sleep(0.1)
        
        # Small delay to prevent excessive CPU usage
        time.sleep(0.05)
            
    print("Aimbot stopped")

if __name__ == "__main__":
    try:
        print(f"Starting aimbot on {platform.system()}...")
        
        # Check dependencies first
        check_dependencies()
        
        # Platform-specific setup
        if platform.system() == 'Darwin':
            print("macOS detected. Make sure to grant accessibility permissions.")
            print("System Preferences > Security & Privacy > Privacy > Accessibility")
        elif platform.system() == 'Windows':
            print("Windows detected. For best results, run as administrator.")
        elif platform.system() == 'Linux':
            if not os.environ.get('DISPLAY'):
                print("Error: No X11 display detected. This application requires X11.")
                sys.exit(1)
            print("Linux detected. Make sure you're running under X11.")
        
        # Start keyboard listener before main function
        if not keyboard_listener.is_alive():
            keyboard_listener.start()
            
        # Small delay to ensure keyboard listener is ready
        time.sleep(0.5)
        
        # Check if keyboard listener started successfully
        if not keyboard_listener.is_alive():
            print("Warning: Keyboard listener failed to start. Key detection may not work.")
        
        aimbot()
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop keyboard listener if it's running
        if keyboard_listener.is_alive():
            keyboard_listener.stop()
