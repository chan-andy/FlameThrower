from src.controllers.maplestory_controller import MapleStoryController
from src.ui.flame_ui import FlameUI
import json
import os

class FlameRerollApp:
    def __init__(self):
        self.controller = MapleStoryController()
        self.settings_file = "flame_settings.json"
        self.load_settings()
        
    def load_settings(self):
        """Load saved settings if they exist"""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                self.saved_settings = json.load(f)
        else:
            self.saved_settings = {
                "flame_type": "Res/Rainbow Flame",
                "thresholds": {
                    "STR": 0, "DEX": 0, "INT": 0, "LUK": 0,
                    "WA": 0, "MA": 0, "STATS%": 0
                }
            }
            
    def save_settings(self, settings):
        """Save current settings to file"""
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=4)
            
    def start_reroll(self, settings):
        """Start the flame reroll process with given settings"""
        print("Starting flame reroll with settings:")
        print(f"Flame Type: {settings['flame_type']}")
        print("Thresholds:")
        for stat, value in settings['thresholds'].items():
            print(f"  {stat}: {value}")
            
        # Save the settings
        self.save_settings(settings)
        
        # TODO: Implement actual flame reroll logic here
        # This is where we'll add the automation logic
        
    def run(self):
        """Start the application"""
        # First, try to find the MapleStory window
        if not self.controller.find_window():
            print("Error: Could not find MapleStory window. Please make sure the game is running.")
            return
            
        # Create and run the UI
        ui = FlameUI(self.start_reroll, self.controller)
        ui.run()

if __name__ == "__main__":
    app = FlameRerollApp()
    app.run() 