import pyautogui
import mss
import numpy as np
import cv2
import time

# Define the target color (adjust this based on the game)
TARGET_COLOR = (255, 0, 0)  # Red in BGR format
COLOR_TOLERANCE = 35  # Dynamically adjustable tolerance

# Minimum contour area threshold
MIN_CONTOUR_AREA = 100

# Capture screen
def capture_screen():
    with mss.mss() as sct:
        # Capture the primary screen (use sct.monitors[0] for the primary monitor)
        screen = sct.grab(sct.monitors[0])  # Full screen capture
        img = np.array(screen)  # Convert to NumPy array
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # Convert to BGR

        # Apply slight blur to reduce noise
        img = cv2.GaussianBlur(img, (5, 5), 0)

        return img

# Find target using color & center of mass detection
def find_target(img):
    screen_width, screen_height = pyautogui.size()
    img_height, img_width, _ = img.shape

    # Define the color range dynamically
    lower = np.array([max(0, c - COLOR_TOLERANCE) for c in TARGET_COLOR], dtype=np.uint8)
    upper = np.array([min(255, c + COLOR_TOLERANCE) for c in TARGET_COLOR], dtype=np.uint8)

    # Create a mask to isolate the target color range
    mask = cv2.inRange(img, lower, upper)

    # Clean up the mask (remove small noise)
    mask = cv2.erode(mask, None, iterations=1)
    mask = cv2.dilate(mask, None, iterations=3)

    # Find contours (objects) in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Filter out small contours
        contours = [cnt for cnt in contours if cv2.contourArea(cnt) > MIN_CONTOUR_AREA]

        if contours:
            # Log the contours to understand if they are correct
            print(f"Detected contours: {len(contours)}")

            # Find the largest contour (assumed to be the target)
            largest = max(contours, key=cv2.contourArea)

            # Get the moments of the contour to find its center
            M = cv2.moments(largest)
            if M["m00"] != 0:
                target_x = int(M["m10"] / M["m00"])
                target_y = int(M["m01"] / M["m00"])
            else:
                return None

            # Convert to full screen coordinates
            target_x = int(target_x * screen_width / img_width)
            target_y = int(target_y * screen_height / img_height)

            return target_x, target_y
    return None

# Move mouse with precision
def move_mouse(target_pos):
    if target_pos:
        print(f"Aiming at {target_pos}")

        # Move smoothly to the target to avoid detection
        pyautogui.moveTo(target_pos[0] + np.random.randint(-5, 5), target_pos[1] + np.random.randint(-5, 5), duration=0.02)

        # Simulate a more natural clicking behavior with a slight delay
        pyautogui.click()
        time.sleep(0.1)  # Short delay to avoid rapid clicking

# Main loop
def aimbot():
    print("Aimbot started. Press Ctrl+C to stop.")
    try:
        while True:
            screen = capture_screen()

            # Check if screen capture is successful (this should never be None)
            if screen is None:
                raise ValueError("Error capturing screen.")

            target = find_target(screen)
            if target:
                move_mouse(target)
            else:
                print("No target detected.")  # Log when no target is found

            # Reduce the loop frequency (increase delay for better performance)
            time.sleep(0.05)  # 20 FPS equivalent; adjust as needed
    except KeyboardInterrupt:
        print("\nAimbot stopped.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    aimbot()
