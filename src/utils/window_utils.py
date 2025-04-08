import win32gui
import win32con

def find_window_by_title(title_substring):
    """
    Find a window by its title substring.
    Returns the window handle if found, None otherwise.
    """
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if title_substring in window_title:
                extra.append(hwnd)
        return True

    windows = []
    win32gui.EnumWindows(callback, windows)
    
    if windows:
        return windows[0]
    return None

def get_window_rect(window_handle):
    """Get the window's position and size"""
    if window_handle:
        # Get window rectangle (includes borders and title bar)
        window_rect = win32gui.GetWindowRect(window_handle)
        
        # Get client rectangle (just the content area)
        client_rect = win32gui.GetClientRect(window_handle)
        
        # Convert client rect to screen coordinates
        client_left, client_top = win32gui.ClientToScreen(window_handle, (0, 0))
        client_right = client_left + client_rect[2]
        client_bottom = client_top + client_rect[3]
        
        return {
            'window': window_rect,
            'client': (client_left, client_top, client_right, client_bottom)
        }
    return None

def get_window_title(window_handle):
    """Get the window's title"""
    if window_handle:
        return win32gui.GetWindowText(window_handle)
    return None 