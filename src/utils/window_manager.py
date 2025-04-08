import win32gui
import win32con
import win32api
import re

class WindowManager:
    def __init__(self):
        self.windows = {}
        
    def get_window(self, window_name):
        """Find a window by name"""
        try:
            print(f"\nLooking for window: {window_name}")
            def callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if window_name.lower() in title.lower():
                        windows.append(hwnd)
                return True
                
            windows = []
            win32gui.EnumWindows(callback, windows)
            
            if windows:
                print(f"Found window handle: {windows[0]}")
                return windows[0]
            else:
                print("Window not found")
                return None
                
        except Exception as e:
            print(f"Error finding window: {str(e)}")
            return None
        
    def get_window_rect(self, hwnd):
        """Get the window rectangle"""
        try:
            print(f"\nGetting window rect for handle: {hwnd}")
            
            # Get the window rectangle
            window_rect = win32gui.GetWindowRect(hwnd)
            print(f"Window rect: {window_rect}")
            
            # Get the client rectangle
            client_rect = win32gui.GetClientRect(hwnd)
            print(f"Client rect: {client_rect}")
            
            # Convert client rect to screen coordinates
            client_left, client_top = win32gui.ClientToScreen(hwnd, (client_rect[0], client_rect[1]))
            client_right, client_bottom = win32gui.ClientToScreen(hwnd, (client_rect[2], client_rect[3]))
            
            # Create the window info dictionary
            window_info = {
                'window': window_rect,
                'client': (client_left, client_top, client_right, client_bottom)
            }
            
            print(f"Window info: {window_info}")
            return window_info
            
        except Exception as e:
            print(f"Error getting window rect: {str(e)}")
            return None
            
    def set_foreground(self, hwnd):
        """Bring window to foreground"""
        if not hwnd:
            return False
            
        try:
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
            # Bring to foreground
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            print(f"Error setting foreground window: {e}")
            return False 