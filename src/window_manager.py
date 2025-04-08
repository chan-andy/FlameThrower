import win32gui
import win32con

class WindowManager:
    def __init__(self):
        self.windows = {}
        
    def get_window(self, title):
        """Find a window by title"""
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if title in window_title:
                    windows[hwnd] = window_title
            return True
            
        win32gui.EnumWindows(callback, self.windows)
        
        if self.windows:
            # Return the first matching window
            hwnd = list(self.windows.keys())[0]
            return Window(hwnd, self.windows[hwnd])
        return None
        
    def get_window_rect(self, window):
        """Get the window and client rectangles"""
        try:
            # Get window rectangle
            window_rect = win32gui.GetWindowRect(window.handle)
            
            # Get client rectangle
            client_rect = win32gui.GetClientRect(window.handle)
            client_left, client_top = win32gui.ClientToScreen(window.handle, (0, 0))
            client_right = client_left + client_rect[2]
            client_bottom = client_top + client_rect[3]
            
            return {
                'window': window_rect,
                'client': (client_left, client_top, client_right, client_bottom)
            }
        except Exception as e:
            print(f"Error getting window rect: {str(e)}")
            return None
            
    def bring_to_front(self, window):
        """Bring the specified window to the front"""
        try:
            # Get the window handle
            hwnd = window.handle
            
            # Bring the window to front
            win32gui.SetForegroundWindow(hwnd)
            
            # Optional: Restore the window if it's minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
            return True
        except Exception as e:
            print(f"Error bringing window to front: {str(e)}")
            return False 