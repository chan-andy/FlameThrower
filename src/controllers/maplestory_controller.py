import time
from src.utils.window_manager import WindowManager
from src.utils.input_controller import InputController
from src.utils.flame_processor import FlameProcessor
import win32api
import win32con
import win32gui
import random

class MapleStoryController:
    def __init__(self):
        self.window_manager = WindowManager()
        self.input_controller = InputController()
        self.flame_processor = FlameProcessor()
        self.window_handle = None
        self.is_running = False
        
    def find_window(self):
        """Find the MapleStory window"""
        self.window_handle = self.window_manager.get_window("MapleStory")
        return self.window_handle is not None
        
    def get_window_info(self):
        """Get information about the MapleStory window"""
        if not self.window_handle:
            self.window_handle = self.window_manager.get_window("MapleStory")
            if not self.window_handle:
                return None
                
        return self.window_manager.get_window_rect(self.window_handle)
        
    def check_thresholds(self, results, thresholds):
        """Check if the flame results meet the threshold requirements"""
        if not results or 'stats' not in results:
            return False
            
        for stat, required_value in thresholds.items():
            if stat == 'STATS%':
                # Handle All Stats percentage
                if 'STATS%' not in results['stats']:
                    return False
                current_value = int(results['stats']['STATS%'].strip('%'))
                if current_value < required_value:
                    return False
            else:
                # Handle regular stats
                if stat not in results['stats']:
                    return False
                if results['stats'][stat] < required_value:
                    return False
                    
        return True
        
    def perform_reroll(self, window_info, reroll_position):
        """Perform a single reroll action"""
        try:
            print("\nPerforming reroll action...")
            print(f"Window info: {window_info}")
            print(f"Reroll position: {reroll_position}")
            
            # Get the client rectangle for relative coordinates
            if 'client' not in window_info:
                print("No client rectangle in window info")
                return False
                
            client_rect = window_info['client']
            width = client_rect[2] - client_rect[0]
            height = client_rect[3] - client_rect[1]
            
            print(f"Client dimensions: {width}x{height}")
            
            # Calculate absolute coordinates from relative position
            abs_x = client_rect[0] + int(reroll_position['x'] * width)
            abs_y = client_rect[1] + int(reroll_position['y'] * height)
            
            print(f"Moving cursor to: ({abs_x}, {abs_y})")
            
            # Get the window handle
            hwnd = self.window_manager.get_window("MapleStory")
            if not hwnd:
                print("Could not find MapleStory window")
                return False
                
            # Bring window to foreground
            print("Bringing window to foreground...")
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.5)
            
            # Move cursor to position
            print("Moving cursor...")
            win32api.SetCursorPos((abs_x, abs_y))
            time.sleep(0.5)
            
            # Click mouse
            print("Clicking mouse...")
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, abs_x, abs_y, 0, 0)
            time.sleep(0.1)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, abs_x, abs_y, 0, 0)
            time.sleep(0.5)
            
            # Press Enter twice
            print("Pressing Enter...")
            win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)  # Press Enter
            time.sleep(0.1)
            win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)  # Release Enter
            time.sleep(0.5)
            
            print("Pressing Enter again...")
            win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)  # Press Enter
            time.sleep(0.1)
            win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)  # Release Enter
            time.sleep(1.5)
            
            print("Reroll action completed")
            return True
            
        except Exception as e:
            print(f"Error performing reroll: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
    def start_reroll(self, settings):
        """Start the flame reroll process"""
        print("\nStarting reroll process with settings:")
        print(f"Flame Type: {settings.get('flame_type')}")
        print("Thresholds:")
        for stat, value in settings.get('thresholds', {}).items():
            print(f"  {stat}: {value}")
        print(f"Tries: {settings.get('tries')}")
        print(f"Reroll Position: {settings.get('reroll_position')}")
        
        if self.is_running:
            print("Reroll process is already running")
            return
            
        self.is_running = True
        try:
            print("\nStep 1: Getting window info...")
            # Get window info
            window_info = self.get_window_info()
            if not window_info:
                print("Could not find MapleStory window")
                return
            print(f"Window info: {window_info}")
            
            remaining_tries = settings['tries']
            print(f"\nStep 2: Starting reroll loop with {remaining_tries} tries...")
            
            while remaining_tries > 0 and self.is_running:
                print(f"\nAttempt {settings['tries'] - remaining_tries + 1} of {settings['tries']}")
                
                # First perform a reroll
                print("Performing reroll...")
                if not self.perform_reroll(window_info, settings['reroll_position']):
                    print("Failed to perform reroll")
                    break
                
                # Wait a bit for the flame results to update
                print("Waiting for results to update...")
                time.sleep(1)
                
                # Process flame results
                print("Processing flame results...")
                result = self.flame_processor.process_flame_results(window_info)
                if result:
                    print("Flame results:", result)
                    
                    # Check if thresholds are met
                    print("Checking thresholds...")
                    if self.check_thresholds(result, settings['thresholds']):
                        print("Thresholds met! Stopping reroll process.")
                        break
                else:
                    print("Could not process flame results")
                    
                remaining_tries -= 1
                print(f"Remaining tries: {remaining_tries}")
                
            if remaining_tries == 0:
                print("Maximum number of tries reached")
                
        except Exception as e:
            print(f"Error during reroll process: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_running = False
            print("Reroll process completed")
            
    def stop_reroll(self):
        """Stop the flame reroll process"""
        self.is_running = False

    def take_screenshot(self):
        """Take a screenshot of the MapleStory window"""
        if not self.window_handle:
            print("No MapleStory window found")
            return False

        window_rect = self.get_window_info()
        if not window_rect:
            print("Could not get window dimensions")
            return False

        return self.screenshot_manager.take_screenshot(window_rect)

    # Input control methods
    def press_key(self, key):
        """Press and release a key"""
        self.input_controller.press_key(key)

    def hold_key(self, key):
        """Hold a key down"""
        self.input_controller.hold_key(key)

    def release_key(self, key):
        """Release a key"""
        self.input_controller.release_key(key)

    def click_mouse(self, button=0):
        """Click a mouse button"""
        self.input_controller.click_mouse(button)

    def move_mouse(self, x, y):
        """Move mouse to absolute coordinates"""
        self.input_controller.move_mouse(x, y) 