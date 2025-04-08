import time
from pynput.keyboard import Controller, Key

class InputController:
    def __init__(self):
        # Initialize keyboard controller
        self.keyboard = Controller()
        
    def press_key(self, key):
        """Press a key"""
        try:
            # Press and release the key
            self.keyboard.press(key)
            time.sleep(0.1)
            self.keyboard.release(key)
            return True
        except Exception as e:
            print(f"Error pressing key {key}: {e}")
            return False
            
    def press_enter(self):
        """Press the Enter key"""
        return self.press_key(Key.enter)
        
    def press_escape(self):
        """Press the Escape key"""
        return self.press_key(Key.esc)
        
    def press_space(self):
        """Press the Space key"""
        return self.press_key(Key.space)
        
    def press_tab(self):
        """Press the Tab key"""
        return self.press_key(Key.tab)
        
    def press_backspace(self):
        """Press the Backspace key"""
        return self.press_key(Key.backspace)
        
    def press_delete(self):
        """Press the Delete key"""
        return self.press_key(Key.delete)
        
    def press_home(self):
        """Press the Home key"""
        return self.press_key(Key.home)
        
    def press_end(self):
        """Press the End key"""
        return self.press_key(Key.end)
        
    def press_page_up(self):
        """Press the Page Up key"""
        return self.press_key(Key.page_up)
        
    def press_page_down(self):
        """Press the Page Down key"""
        return self.press_key(Key.page_down)
        
    def press_arrow_up(self):
        """Press the Up Arrow key"""
        return self.press_key(Key.up)
        
    def press_arrow_down(self):
        """Press the Down Arrow key"""
        return self.press_key(Key.down)
        
    def press_arrow_left(self):
        """Press the Left Arrow key"""
        return self.press_key(Key.left)
        
    def press_arrow_right(self):
        """Press the Right Arrow key"""
        return self.press_key(Key.right)
        
    def press_function_key(self, number):
        """Press a function key (F1-F12)"""
        if 1 <= number <= 12:
            key_name = f'f{number}'
            return self.press_key(getattr(Key, key_name))
        return False 