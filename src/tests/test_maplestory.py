from ..controllers.maplestory_controller import MapleStoryController

def test_maplestory_controller():
    """Test function to verify MapleStory controller functionality"""
    controller = MapleStoryController()
    
    print("Testing MapleStory window detection...")
    if controller.find_window():
        print("✓ Successfully found MapleStory window")
        
        # Get window information
        window_info = controller.get_window_info()
        if window_info:
            print(f"Window title: {window_info['title']}")
            print(f"Window position and size: {window_info['rect']}")
            
            # Test screenshot
            print("\nAttempting to take screenshot...")
            if controller.take_screenshot():
                print("✓ Screenshot test successful")
            else:
                print("✗ Screenshot test failed")
    else:
        print("✗ Could not find MapleStory window. Make sure the game is running.")

if __name__ == "__main__":
    test_maplestory_controller() 