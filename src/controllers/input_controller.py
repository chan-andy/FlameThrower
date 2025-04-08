from interception import Interception

class InputController:
    def __init__(self):
        self.interception = Interception()
        
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