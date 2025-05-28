import pyautogui
import mss
import numpy as np
import cv2
import time

# Define the target color (adjust this based on the game)
TARGET_COLOR = (255, 0, 0)  # Red in BGR format
COLOR_TOLERANCE = 75  # Greatly increased tolerance for maximum detection
MIN_CONTOUR_AREA = 20  # Significantly reduced to catch even tiny targets
TARGET_COLORS = [
    (255, 0, 0),    # Red
    (240, 10, 10),  # Slightly different red
    (220, 0, 0)     # Darker red
]

# Capture screen
def capture_screen():
    with mss.mss() as sct:
        screen = sct.grab(sct.monitors[0])  # Full screen capture
        img = np.array(screen)  # Convert to NumPy array
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # Convert to BGR
        img = cv2.GaussianBlur(img, (5, 5), 0)
        return img

# Find target using color detection
def find_target(img):
    screen_width, screen_height = pyautogui.size()
    img_height, img_width, _ = img.shape

    # Create a combined mask from multiple color ranges
    combined_mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
    # Process each target color
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

    if contours:
        # Filter out small contours
        contours = [cnt for cnt in contours if cv2.contourArea(cnt) > MIN_CONTOUR_AREA]

        if contours:
            # Find the largest contour
            largest = max(contours, key=cv2.contourArea)

            # Get the moments of the contour
            M = cv2.moments(largest)
            if M["m00"] != 0:
                target_x = M["m10"] / M["m00"]
                target_y = M["m01"] / M["m00"]
                
                # Headshot targeting
                x, y, w, h = cv2.boundingRect(largest)
                target_y = y + h * 0.2  # Target the top 20% of the contour
            else:
                return None

            # Convert to screen coordinates
            target_x = target_x * screen_width / img_width
            target_y = target_y * screen_height / img_height

            return target_x, target_y

    return None

# Move mouse and fire
def move_mouse(target_pos):
    if target_pos:
        print(f"Aiming at {target_pos}")
        pyautogui.moveTo(target_pos[0], target_pos[1], duration=0.01)
        pyautogui.click()

# Simple aimbot that runs once when 'y' key is pressed
def aimbot():
    print("Aimbot started. Press Ctrl+C to stop.")
    print("Press 'y' key when ready to fire.")
    
    while True:
        key = input()
        if key.lower() == 'y':
            print("Scanning for targets...")
            screen = capture_screen()
            target = find_target(screen)
            
            if target:
                print("Target found! Firing...")
                move_mouse(target)
                print("Shot fired!")
            else:
                print("No targets detected.")
        elif key.lower() == 'q':
            print("Exiting...")
            break

if __name__ == "__main__":
    aimbot()
