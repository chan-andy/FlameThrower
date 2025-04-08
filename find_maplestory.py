import win32gui
import win32con
from interception import Interception
from PIL import ImageGrab
import time
import os
from datetime import datetime

class MapleStoryController:
    def __init__(self):
        self.interception = Interception()
        self.window_handle = None
        self.images_dir = "Images"
        
    def _get_screenshot_path(self):
        """Generate the path for saving screenshots based on current date and time"""
        # Get current date and time
        now = datetime.now()
        
        # Create date-based folder path
        date_folder = now.strftime("%Y-%m-%d")
        full_path = os.path.join(self.images_dir, date_folder)
        
        # Create directories if they don't exist
        os.makedirs(full_path, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = now.strftime("%H-%M-%S")
        filename = f"maplestory_{timestamp}.png"
        
        return os.path.join(full_path, filename)
        
    def find_maplestory_window(self):
        """
        Find the MapleStory window by its class name and title.
        Returns the window handle if found, None otherwise.
        """
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if "MapleStory" in window_title:
                    extra.append(hwnd)
            return True

        windows = []
        win32gui.EnumWindows(callback, windows)
        
        if windows:
            self.window_handle = windows[0]
            return self.window_handle
        return None

    def press_key(self, key):
        """Press and release a key"""
        self.interception.send_key(key, 0)  # 0 for key down
        self.interception.send_key(key, 1)  # 1 for key up

    def hold_key(self, key):
        """Hold a key down"""
        self.interception.send_key(key, 0)  # 0 for key down

    def release_key(self, key):
        """Release a key"""
        self.interception.send_key(key, 1)  # 1 for key up

    def click_mouse(self, button=0):  # 0 for left button
        """Click a mouse button"""
        self.interception.send_mouse_button(button, 0)  # 0 for button down
        self.interception.send_mouse_button(button, 1)  # 1 for button up

    def move_mouse(self, x, y):
        """Move mouse to absolute coordinates"""
        self.interception.send_mouse_move(x, y)

    def get_window_rect(self):
        """Get the window's position and size"""
        if self.window_handle:
            return win32gui.GetWindowRect(self.window_handle)
        return None

    def take_screenshot(self):
        """Take a screenshot of the MapleStory window and save it with timestamp"""
        if not self.window_handle:
            print("No MapleStory window found")
            return False

        # Get window dimensions
        rect = self.get_window_rect()
        if not rect:
            print("Could not get window dimensions")
            return False

        # Generate save path
        save_path = self._get_screenshot_path()

        # Take screenshot of the window region
        screenshot = ImageGrab.grab(bbox=rect)
        screenshot.save(save_path)
        print(f"Screenshot saved to {save_path}")
        return True

def test_window_detection():
    """Test function to verify window detection and screenshot capabilities"""
    controller = MapleStoryController()
    
    print("Testing MapleStory window detection...")
    window_handle = controller.find_maplestory_window()
    
    if window_handle:
        print(f"✓ Successfully found MapleStory window (handle: {window_handle})")
        
        # Get window information
        title = win32gui.GetWindowText(window_handle)
        rect = controller.get_window_rect()
        print(f"Window title: {title}")
        print(f"Window position and size: {rect}")
        
        # Test screenshot
        print("\nAttempting to take screenshot...")
        if controller.take_screenshot():
            print("✓ Screenshot test successful")
        else:
            print("✗ Screenshot test failed")
    else:
        print("✗ Could not find MapleStory window. Make sure the game is running.")

if __name__ == "__main__":
    test_window_detection() 