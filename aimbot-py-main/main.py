import pyautogui
import mss
import numpy as np
import cv2
import time
import sys
import platform
import os
import threading
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
AIM_KEY = 'a'       # Key to aim at the last found target
EXIT_KEY = 'q'      # Key to exit

# Capture screen with region option for better performance
def capture_screen(region=None):
    with mss.mss() as sct:
        if region:
            monitor = {"top": region[1], "left": region[0], 
                      "width": region[2], "height": region[3]}
            screen = sct.grab(monitor)
        else:
            screen = sct.grab(sct.monitors[0])
            
        img = np.array(screen)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        img = cv2.GaussianBlur(img, (5, 5), 0)
        return img

# Find target using color detection
def find_target(img):
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
    
    return target_x, target_y, (x, y, w, h)  # Return target coords and bounding box

# Move mouse to target (no click)
def aim_at_target(target_pos):
    if not target_pos:
        return False
        
    x, y = target_pos[0], target_pos[1]
    pyautogui.moveTo(x, y, duration=0.01)
    return True

# Global variables for key states
key_states = {
    SCAN_KEY: False,
    AIM_KEY: False,
    EXIT_KEY: False
}
key_lock = threading.Lock()

# Keyboard listener setup
def on_press(key):
    try:
        k = key.char.lower()
        with key_lock:
            if k in key_states:
                key_states[k] = True
    except AttributeError:
        pass

def on_release(key):
    try:
        k = key.char.lower()
        with key_lock:
            if k in key_states:
                key_states[k] = False
    except AttributeError:
        pass

# Start keyboard listener
keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
keyboard_listener.start()

# Check if key is pressed
def key_pressed():
    with key_lock:
        if key_states[SCAN_KEY]:
            key_states[SCAN_KEY] = False  # Reset after reading
            return SCAN_KEY
        elif key_states[AIM_KEY]:
            key_states[AIM_KEY] = False  # Reset after reading
            return AIM_KEY
        elif key_states[EXIT_KEY]:
            return EXIT_KEY
    return None

# Main aimbot function
def aimbot():
    print("Aimbot started!")
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
        
        # Small delay to prevent excessive CPU usage
        time.sleep(0.05)
            
    print("Aimbot stopped")

if __name__ == "__main__":
    print(f"Running on {platform.system()}")
    try:
        aimbot()
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Stop keyboard listener
        keyboard_listener.stop()
