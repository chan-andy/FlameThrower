import os
from datetime import datetime
from PIL import ImageGrab

class ScreenshotManager:
    def __init__(self, base_dir="Images"):
        self.base_dir = base_dir
        
    def _get_screenshot_path(self):
        """Generate the path for saving screenshots based on current date and time"""
        # Get current date and time
        now = datetime.now()
        
        # Create date-based folder path
        date_folder = now.strftime("%Y-%m-%d")
        full_path = os.path.join(self.base_dir, date_folder)
        
        # Create directories if they don't exist
        os.makedirs(full_path, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = now.strftime("%H-%M-%S")
        filename = f"maplestory_{timestamp}.png"
        
        return os.path.join(full_path, filename)
    
    def take_screenshot(self, window_rect):
        """Take a screenshot of the specified window region"""
        if not window_rect:
            print("No window region specified")
            return False

        # Generate save path
        save_path = self._get_screenshot_path()

        # Take screenshot of the window region
        screenshot = ImageGrab.grab(bbox=window_rect)
        screenshot.save(save_path)
        print(f"Screenshot saved to {save_path}")
        return True 