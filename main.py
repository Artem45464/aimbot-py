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

# Configuration
TARGET_COLORS = [
    # Red colors
    (255, 0, 0),    # Pure red
    (240, 10, 10),  # Slightly different red
    (220, 0, 0),    # Darker red
    (255, 50, 50),  # Light red
    (200, 0, 0),    # Very dark red
    (255, 100, 100), # Pink-red
    
    # Green colors
    (0, 255, 0),    # Pure green
    (0, 220, 0),    # Darker green
    (50, 255, 50),  # Light green
    (0, 200, 0),    # Very dark green
    (100, 255, 100), # Light green
    
    # Blue colors
    (0, 0, 255),    # Pure blue
    (0, 0, 220),    # Darker blue
    (50, 50, 255),  # Light blue
    (0, 0, 200),    # Very dark blue
    (100, 100, 255), # Light blue
    
    # Yellow colors
    (255, 255, 0),  # Pure yellow
    (220, 220, 0),  # Darker yellow
    (255, 255, 50), # Light yellow
    
    # Purple/Magenta colors
    (255, 0, 255),  # Pure magenta
    (220, 0, 220),  # Darker magenta
    (255, 50, 255), # Light magenta
    (180, 0, 180),  # Dark purple
    
    # Cyan colors
    (0, 255, 255),  # Pure cyan
    (0, 220, 220),  # Darker cyan
    (50, 255, 255), # Light cyan
    
    # Orange colors
    (255, 165, 0),  # Pure orange
    (255, 140, 0),  # Dark orange
    (255, 190, 0),  # Light orange
    
    # White/Gray colors (for white targets)
    (255, 255, 255), # Pure white
    (220, 220, 220), # Light gray
    (200, 200, 200)  # Medium gray
]
COLOR_TOLERANCE = 60  # Adjusted for multi-color detection
MIN_CONTOUR_AREA = 15 # Reduced to detect smaller targets
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
        
        # Target the center of the top 10% of the contour (more precise headshot)
        target_x = M["m10"] / M["m00"]  # Center X position
        target_y = y + h * 0.10  # Target upper portion for better precision (headshot)
        
        # Convert to screen coordinates
        target_x = target_x * screen_width / img_width
        target_y = target_y * screen_height / img_height
        
        # Apply Retina display scaling correction if needed
        if platform.system() == 'Darwin' and is_retina_display:
            # On Retina displays, we need to divide by 2 to get the correct screen position
            target_x /= 2
            target_y /= 2
        
        return target_x, target_y, (x, y, w, h)  # Return target coords and bounding box
    except Exception as e:
        print(f"Error in target detection: {e}")
        return None

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
                # No need to import ctypes here since it's imported at the top level
                # Use SetCursorPos for immediate positioning
                x_int, y_int = int(round(x)), int(round(y))
                ctypes.windll.user32.SetCursorPos(x_int, y_int)
                
                # Double-check position with a second call for accuracy
                time.sleep(0.01)
                ctypes.windll.user32.SetCursorPos(x_int, y_int)
            except Exception:
                # Fall back to pyautogui if Win32 API fails
                # Use zero duration for immediate movement
                pyautogui.moveTo(x, y, duration=0)
        elif platform.system() == 'Darwin':  # macOS
            try:
                # For macOS, use Quartz for more accurate positioning
                # No need to import here since we imported at the top level
                main_display = CGMainDisplayID()
                main_height = CGDisplayPixelsHigh(main_display)
                
                # Convert to Quartz coordinate system (origin at bottom left)
                quartz_y = main_height - y
                
                # Use Quartz for mouse movement - double call for accuracy
                # Store coordinates to ensure consistency between calls
                quartz_x = float(x)
                quartz_y = float(quartz_y)
                CGPostMouseEvent((quartz_x, quartz_y), True, 1, False)
                time.sleep(0.01)
                CGPostMouseEvent((quartz_x, quartz_y), True, 1, False)
            except Exception as e:
                # Fall back to pyautogui if Quartz fails
                print(f"Quartz mouse movement failed: {e}, falling back to pyautogui")
                pyautogui.moveTo(x, y, duration=0)
        else:
            # Use zero duration for Linux for immediate movement
            try:
                # For Linux, ensure we're using integers for better compatibility
                pyautogui.moveTo(int(round(x)), int(round(y)), duration=0)
            except Exception as e:
                print(f"Linux mouse movement error: {e}")
                # Fallback to float coordinates if integer conversion fails
                pyautogui.moveTo(x, y, duration=0)
        return True
    except Exception as e:
        print(f"Aiming error: {e}")
        return False

# Global variables for key states
key_states = {
    SCAN_KEY: False,
    AIM_KEY: False,
    EXIT_KEY: False
}
last_key_time = {
    SCAN_KEY: 0,
    AIM_KEY: 0,
    EXIT_KEY: 0
}
# Track which keys should actually trigger actions
action_keys = [SCAN_KEY, AIM_KEY, EXIT_KEY]
key_lock = threading.Lock()

# Keyboard listener setup
def on_press(key):
    try:
        k = key.char.lower() if hasattr(key, 'char') else None
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
    except (TypeError):
        # Handle TypeError (can't convert to lower)
        pass

def on_release(key):
    try:
        k = key.char.lower() if hasattr(key, 'char') else None
        if k is None:
            return
            
        with key_lock:
            if k in key_states:
                key_states[k] = False
    except (TypeError):
        # Handle TypeError (can't convert to lower)
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
                    max(0, int(x1 - padding)),
                    max(0, int(y1 - padding)),
                    max(1, int(w + padding * 2)),
                    max(1, int(h + padding * 2))
                )
                
                # Enhanced aiming with multiple attempts for accuracy
                # First aim attempt - move quickly to the target
                aim_at_target(current_target)
                
                # Small pause to let the system process the movement
                time.sleep(0.02)  # Reduced delay for faster response
                
                # Second aim attempt for micro-adjustment and better accuracy
                aim_at_target(current_target)
                
                # Third aim attempt for perfect precision
                time.sleep(0.01)
                aim_at_target(current_target)
                print("Aimed at target")
                
                # Brief pause after finding a target
                time.sleep(0.05)  # Reduced delay for faster response
            else:
                # Only print "scanning" message occasionally to avoid spam
                if scan_count % 20 == 0:
                    print("Scanning...")
                    scan_count = 0
                    
                # If we've lost the target for too long, reset region to scan full screen
                if last_region and scan_count > 30:
                    last_region = None
                    print("Target lost, scanning full screen")
        
        # Aim at target when aim key is pressed
        if key == AIM_KEY and current_target:
            print(f"Aiming at target ({int(current_target[0])}, {int(current_target[1])})")
            aim_at_target(current_target)
            # Add a small delay to prevent multiple rapid movements
            time.sleep(0.05)  # Reduced for faster response
        
        # Small delay to prevent excessive CPU usage
        time.sleep(0.01)  # Reduced for more frequent scanning
            
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
            # Try to start it one more time
            try:
                # Create a new listener instance
                new_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
                new_listener.start()
                time.sleep(0.5)
                if not new_listener.is_alive():
                    print("Error: Could not start keyboard listener. Key detection will not work.")
                else:
                    # Replace the old listener with the new one
                    keyboard_listener.stop()
                    keyboard_listener = new_listener
            except Exception as e:
                print(f"Error restarting keyboard listener: {e}")
        
        aimbot()
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop keyboard listener if it's running
        try:
            if keyboard_listener and keyboard_listener.is_alive():
                keyboard_listener.stop()
        except Exception as e:
            print(f"Error stopping keyboard listener: {e}")
