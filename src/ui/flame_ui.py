import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Callable
from PIL import ImageGrab, ImageTk, Image
import os
from datetime import datetime
import pytesseract
import mss
import win32gui
import win32con
import win32api
import interception
import threading  # Add threading for keyboard monitoring
import time

class RegionSelector:
    def __init__(self, on_region_selected, window_info, parent):
        self.root = tk.Toplevel(parent)
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.attributes('-alpha', 0.3)  # Make window semi-transparent
        self.root.attributes('-topmost', True)  # Keep window on top
        
        # Get client rectangle (just the content area)
        client_rect = window_info['client']
        client_width = client_rect[2] - client_rect[0]
        client_height = client_rect[3] - client_rect[1]
        
        # Position the window over the MapleStory window's client area
        self.root.geometry(f"{client_width}x{client_height}+{client_rect[0]}+{client_rect[1]}")
        
        # Create a canvas that fills the entire window
        self.canvas = tk.Canvas(self.root, cursor="cross", bg='white', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.on_region_selected = on_region_selected
        self.client_rect = client_rect
        
        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", self.on_escape)
        
    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=2
        )
        
    def on_drag(self, event):
        self.canvas.coords(
            self.rect,
            self.start_x, self.start_y, event.x, event.y
        )
        
    def on_release(self, event):
        x1, y1, x2, y2 = self.canvas.coords(self.rect)
        
        # Convert to absolute screen coordinates
        region = {
            'left': self.client_rect[0] + min(x1, x2),
            'top': self.client_rect[1] + min(y1, y2),
            'right': self.client_rect[0] + max(x1, x2),
            'bottom': self.client_rect[1] + max(y1, y2)
        }
        
        # Print debug information
        print(f"Selected region (absolute): {region}")
        print(f"Client rect: {self.client_rect}")
        print(f"Canvas coordinates: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
        
        self.on_region_selected(region)
        self.root.destroy()
        
    def on_escape(self, event):
        self.root.destroy()
        
    def run(self):
        self.root.wait_window()

class PreviewWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Flame Region Preview")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Create image label
        self.image_label = ttk.Label(self.window)
        self.image_label.pack(padx=10, pady=10)
        
        # Create OCR text display
        self.ocr_text = tk.Text(self.window, height=5, width=40)
        self.ocr_text.pack(padx=10, pady=10)
        
        # Keep reference to the photo to prevent garbage collection
        self.photo = None
        
    def update_preview(self, image, ocr_text):
        # Convert PIL image to PhotoImage
        self.photo = ImageTk.PhotoImage(image)
        self.image_label.configure(image=self.photo)
        
        # Update OCR text
        self.ocr_text.delete(1.0, tk.END)
        self.ocr_text.insert(1.0, ocr_text)
        
    def on_close(self):
        self.window.destroy()

class FlameUI:
    def __init__(self, on_start: Callable[[Dict], None], controller):
        self.root = tk.Tk()
        self.root.title("Flame Thrower")
        self.on_start = on_start
        self.controller = controller
        
        # Initialize interception
        self.interception = interception
        self.interception.auto_capture_devices(keyboard=True, mouse=True)
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.main_frame.grid_columnconfigure(0, weight=1)  # Left column
        self.main_frame.grid_columnconfigure(1, weight=1)  # Right column
        
        # Threshold inputs
        self._create_threshold_inputs()
        
        # Region adjustment frame
        self._create_region_adjustment()
        
        # Instructions and Results display frames
        self._create_right_column()
        
        # Add some padding at the bottom
        ttk.Label(self.main_frame, text="").grid(row=11, column=0, pady=5)
        
        # Preview window
        self.preview_window = None
        
        # Load saved settings
        self._load_settings()
        
        # Add status label
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.grid(row=13, column=0, columnspan=2, pady=5)
        
        # Add keyboard interrupt flag
        self.should_stop = False
        self.keyboard_thread = None
        
        # Add animation flag
        self.is_animating = False
        
        # Create ttk styles for button animation
        self.style = ttk.Style()
        self.style.configure('Running.TButton', foreground='red')
        self.style.configure('Normal.TButton', foreground='black')
        
    def _create_right_column(self):
        """Create the right column containing instructions and results"""
        # Instructions frame
        instructions_frame = ttk.LabelFrame(self.main_frame, text="Instructions", padding="5")
        instructions_frame.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Create instructions text
        instructions = [
            "1. Manually roll a flame first to bring up Flame Result UI in game.",
            "2. Select Region to select the 'Result' window of the flame",
            "3. Test Screenshot to ensure it captures and extracts the current result properly.",
            "4. 'Set Reroll Position' to save cursor position of where the 'Reroll' button is in game.",
            "5. Set Thresholds and Delay settings."
        ]
        
        # Add each instruction as a label
        for i, instruction in enumerate(instructions):
            ttk.Label(instructions_frame, text=instruction, wraplength=400).pack(padx=5, pady=2, anchor=tk.W)
        
        # Results display frame
        results_frame = ttk.LabelFrame(self.main_frame, text="Results", padding="5")
        results_frame.grid(row=1, column=1, rowspan=6, sticky=(tk.N, tk.S, tk.E, tk.W), pady=5, padx=(10, 0))
        
        # Configure results frame to expand vertically
        results_frame.grid_rowconfigure(0, weight=1)
        
        # Create text widget for results
        self.results_text = tk.Text(results_frame, height=6, width=50, wrap=tk.WORD)
        self.results_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.results_text.insert(1.0, "Results will appear here...")
        self.results_text.config(state=tk.DISABLED)  # Make it read-only
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)
        
        # Create buttons frame under results
        buttons_frame = ttk.Frame(results_frame)
        buttons_frame.pack(pady=5)
        
        # Roll button
        self.start_button = ttk.Button(
            buttons_frame,
            text="Roll",
            command=self._on_start_clicked
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Force Stop button
        self.stop_button = ttk.Button(
            buttons_frame,
            text="Force Stop",
            command=self._on_force_stop
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
    def _create_threshold_inputs(self):
        """Create the threshold inputs section"""
        # Threshold frame
        threshold_frame = ttk.LabelFrame(self.main_frame, text="Threshold Settings", padding="5")
        threshold_frame.grid(row=0, column=0, sticky=tk.EW, pady=5)
        
        # Create checkboxes and entries for each stat
        self.thresholds = {}
        self.threshold_vars = {}  # For checkboxes
        self.threshold_values = {}  # For entry values
        
        stats = ["STR", "DEX", "INT", "LUK", "STATS%"]
        for i, stat in enumerate(stats):
            # Create checkbox
            var = tk.BooleanVar(value=False)
            self.threshold_vars[stat] = var
            cb = ttk.Checkbutton(
                threshold_frame,
                text=stat if stat != "STATS%" else "All Stats %",
                variable=var,
                command=lambda s=stat: self._on_threshold_toggle(s)
            )
            cb.grid(row=i//2, column=(i%2)*2, padx=5, pady=2, sticky=tk.W)
            
            # Create entry
            value_var = tk.StringVar(value="0")
            self.threshold_values[stat] = value_var
            entry = ttk.Entry(threshold_frame, textvariable=value_var, width=5, state='disabled')
            entry.grid(row=i//2, column=(i%2)*2+1, padx=5, pady=2)
            self.thresholds[stat] = entry
            
        # Add Tries field
        ttk.Label(threshold_frame, text="Tries:").grid(row=3, column=0, padx=5, pady=2, sticky=tk.W)
        self.tries_var = tk.StringVar(value="10")
        ttk.Entry(threshold_frame, textvariable=self.tries_var, width=5).grid(row=3, column=1, padx=5, pady=2)
        
        # Add Save button
        self.save_button = ttk.Button(
            threshold_frame,
            text="Save Settings",
            command=self._on_save_settings
        )
        self.save_button.grid(row=3, column=2, columnspan=2, padx=5, pady=2)
        
        # Create Delay Settings frame
        delay_frame = ttk.LabelFrame(self.main_frame, text="Delay Settings", padding="5")
        delay_frame.grid(row=1, column=0, sticky=tk.EW, pady=5)
        
        # Action delay
        ttk.Label(delay_frame, text="Action Delay:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.action_delay_var = tk.StringVar(value="0.5")
        ttk.Entry(delay_frame, textvariable=self.action_delay_var, width=5).grid(row=0, column=1, padx=5, pady=2)
        
        # Parse delay
        ttk.Label(delay_frame, text="Parse Delay:").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        self.parse_delay_var = tk.StringVar(value="1.5")
        ttk.Entry(delay_frame, textvariable=self.parse_delay_var, width=5).grid(row=0, column=3, padx=5, pady=2)
        
        # Save button for delay settings
        self.save_delay_button = ttk.Button(
            delay_frame,
            text="Save Delays",
            command=self._on_save_delay_settings
        )
        self.save_delay_button.grid(row=0, column=4, padx=5, pady=2)
        
    def _on_threshold_toggle(self, stat):
        """Enable/disable threshold entry based on checkbox state"""
        if self.threshold_vars[stat].get():
            self.thresholds[stat].configure(state='normal')
        else:
            self.thresholds[stat].configure(state='disabled')
            self.threshold_values[stat].set("0")
            
    def _on_save_settings(self):
        """Save the current threshold settings"""
        try:
            # Collect all settings
            settings = {
                "thresholds": {},
                "tries": int(self.tries_var.get()),
                "reroll_position": {
                    "x": float(self.x_var.get()),
                    "y": float(self.y_var.get())
                },
                "capture_region": {
                    "left": float(self.left_var.get()),
                    "top": float(self.top_var.get()),
                    "right": float(self.right_var.get()),
                    "bottom": float(self.bottom_var.get())
                }
            }
            
            # Get enabled thresholds
            for stat, var in self.threshold_vars.items():
                if var.get():
                    try:
                        value = int(self.threshold_values[stat].get())
                        if value < 0:
                            messagebox.showerror("Error", f"{stat} threshold must be non-negative")
                            return
                        settings["thresholds"][stat] = value
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid {stat} threshold value")
                        return
            
            if not settings["thresholds"]:
                messagebox.showerror("Error", "Please select at least one threshold")
                return
                
            # Save settings to file
            import json
            with open("flame_settings.json", "w") as f:
                json.dump(settings, f, indent=4)
                
            messagebox.showinfo("Success", "Settings saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            
    def _on_save_delay_settings(self):
        """Save the current delay settings"""
        try:
            # Validate and save delay settings
            parse_delay = float(self.parse_delay_var.get())
            action_delay = float(self.action_delay_var.get())
            
            if parse_delay <= 0 or action_delay <= 0:
                messagebox.showerror("Error", "Delay values must be positive")
                return
                
            # Save settings to file
            import json
            with open("flame_settings.json", "r") as f:
                settings = json.load(f)
                
            settings["delays"] = {
                "parse": parse_delay,
                "action": action_delay
            }
            
            with open("flame_settings.json", "w") as f:
                json.dump(settings, f, indent=4)
                
            messagebox.showinfo("Success", "Delay settings saved successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid delay values")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save delay settings: {str(e)}")
            
    def _load_settings(self):
        """Load settings from file"""
        try:
            import json
            import os
            
            if not os.path.exists("flame_settings.json"):
                return
                
            with open("flame_settings.json", "r") as f:
                settings = json.load(f)
                
            # Load thresholds
            if "thresholds" in settings:
                for stat, value in settings["thresholds"].items():
                    if stat in self.threshold_vars:
                        self.threshold_vars[stat].set(True)
                        self.threshold_values[stat].set(str(value))
                        self.thresholds[stat].configure(state='normal')
                        
            # Load tries
            if "tries" in settings:
                self.tries_var.set(str(settings["tries"]))
                
            # Load reroll position
            if "reroll_position" in settings:
                pos = settings["reroll_position"]
                self.x_var.set(str(pos["x"]))
                self.y_var.set(str(pos["y"]))
                
            # Load capture region
            if "capture_region" in settings:
                region = settings["capture_region"]
                self.left_var.set(str(region["left"]))
                self.top_var.set(str(region["top"]))
                self.right_var.set(str(region["right"]))
                self.bottom_var.set(str(region["bottom"]))
                
            # Load delay settings
            if "delays" in settings:
                delays = settings["delays"]
                self.parse_delay_var.set(str(delays["parse"]))
                self.action_delay_var.set(str(delays["action"]))
                
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
            
    def _update_region_coordinates(self):
        """Update the flame processor's region coordinates"""
        try:
            self.controller.flame_processor.result_region = {
                'left': float(self.left_var.get()),
                'top': float(self.top_var.get()),
                'right': float(self.right_var.get()),
                'bottom': float(self.bottom_var.get())
            }
        except ValueError:
            print("Invalid region coordinates")
            
    def _show_preview(self, image):
        """Show the preview window with the screenshot"""
        # Close existing preview if it exists
        if self.preview_window:
            try:
                self.preview_window.window.destroy()
            except:
                pass  # Window might already be closed
        
        # Create new preview window
        self.preview_window = PreviewWindow(self.root)
        
        # Process the image with OCR
        results = self.controller.flame_processor.parse_flame_results(image)
        
        # Update preview with results
        if results:
            # Format the results text
            ocr_text = "Extracted Stats:\n"
            
            # Add each stat with proper formatting
            for stat, value in results['stats'].items():
                if stat == 'STATS%':
                    ocr_text += f"All Stats: {value}\n"
                else:
                    ocr_text += f"{stat}: {value}\n"
            
            # Add attack and CP increases if present
            if results['attack_increase'] is not None:
                ocr_text += f"Attack Increase: {results['attack_increase']}\n"
            if results['cp_increase'] is not None:
                ocr_text += f"CP Increase: {results['cp_increase']}\n"
            
            # Add raw OCR text at the bottom
            ocr_text += f"\nRaw OCR text:\n{results['raw_text']}"
        else:
            ocr_text = "Failed to process image"
            
        # Update the preview window
        self.preview_window.update_preview(image, ocr_text)
        
    def _on_test_screenshot(self):
        """Handle test screenshot button click"""
        try:
            print("Testing screenshot...")
            
            # Get the MapleStory window
            window = self.controller.window_manager.get_window("MapleStory")
            if not window:
                print("Could not find MapleStory window")
                messagebox.showerror("Error", "Could not find MapleStory window. Make sure MapleStory is running.")
                return
            
            print(f"Found MapleStory window: {window}")
            
            # Get the window rectangle
            window_rect = self.controller.window_manager.get_window_rect(window)
            if not window_rect:
                print("Could not get window rectangle")
                messagebox.showerror("Error", "Could not get window dimensions")
                return
                
            print(f"Window rectangle: {window_rect}")
            
            # Get the client rectangle for relative coordinates
            if 'client' not in window_rect:
                print("No client rectangle in window info")
                messagebox.showerror("Error", "Could not get client area dimensions")
                return
                
            client_rect = window_rect['client']
            width = client_rect[2] - client_rect[0]
            height = client_rect[3] - client_rect[1]
            
            print(f"Client rectangle: {client_rect}")
            print(f"Client dimensions: {width}x{height}")
            
            # Get the region coordinates from the input fields
            try:
                left = float(self.left_var.get())
                top = float(self.top_var.get())
                right = float(self.right_var.get())
                bottom = float(self.bottom_var.get())
            except ValueError:
                print("Invalid region coordinates")
                messagebox.showerror("Error", "Invalid region coordinates")
                return
                
            # Convert relative coordinates to absolute within the client area
            region = {
                'left': client_rect[0] + int(left * width),
                'top': client_rect[1] + int(top * height),
                'right': client_rect[0] + int(right * width),
                'bottom': client_rect[1] + int(bottom * height)
            }
            
            print(f"Capture region (absolute): {region}")
            
            # Create monitor dict for mss
            monitor = {
                'left': region['left'],
                'top': region['top'],
                'width': region['right'] - region['left'],
                'height': region['bottom'] - region['top']
            }
            
            print(f"Monitor settings: {monitor}")
            
            # Take screenshot of the region
            with mss.mss() as sct:
                # Take the screenshot
                screenshot = sct.grab(monitor)
                
                # Convert the screenshot to a PIL Image
                image = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                
                # Create the directory structure
                base_dir = "results/test"
                today = datetime.now().strftime("%Y-%m-%d")
                save_dir = os.path.join(base_dir, today)
                
                # Create directories if they don't exist
                os.makedirs(save_dir, exist_ok=True)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%H-%M-%S")
                filename = f"test_screenshot_{timestamp}.png"
                filepath = os.path.join(save_dir, filename)
                
                # Save the image
                image.save(filepath)
                print(f"Screenshot saved to: {filepath}")
                
                print(f"Screenshot size: {image.size}")
                
                # Show the preview
                self._show_preview(image)
            
        except Exception as e:
            print(f"Error in test screenshot: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def _move_cursor_smoothly(self, start_x, start_y, target_x, target_y, steps=20, delay=0.01):
        """Move cursor smoothly from start to target position"""
        import math
        
        # Calculate step sizes
        dx = (target_x - start_x) / steps
        dy = (target_y - start_y) / steps
        
        # Move cursor in small steps
        for i in range(steps):
            # Use easing function for more natural movement
            t = i / steps
            # Ease-out cubic function
            t = 1 - math.pow(1 - t, 3)
            
            # Calculate current position
            current_x = start_x + dx * i
            current_y = start_y + dy * i
            
            # Move cursor to current position
            self.interception.move_to(int(current_x), int(current_y))
            time.sleep(delay)
            
        # Ensure final position is exactly at target
        self.interception.move_to(int(target_x), int(target_y))
        
    def _perform_click_sequence(self, x, y):
        """Perform the click and enter sequence"""
        import time
        import os
        from datetime import datetime
        
        print(f"Starting click sequence at ({x}, {y})")
        
        # Get delay values from UI
        parse_delay = float(self.parse_delay_var.get())
        action_delay = float(self.action_delay_var.get())
        
        # Move cursor to position
        current_x, current_y = win32api.GetCursorPos()
        print(f"Current cursor position: ({current_x}, {current_y})")
        self._move_cursor_smoothly(current_x, current_y, x, y)
        
        # Verify cursor moved
        new_x, new_y = win32api.GetCursorPos()
        print(f"Cursor position after movement: ({new_x}, {new_y})")
        
        # Click once
        print("Performing click...")
        try:
            # First try to bring window to front
            window = self.controller.window_manager.get_window("MapleStory")
            if window:
                print(f"Bringing window to front: {window}")
                try:
                    # Try to bring window to front
                    win32gui.SetForegroundWindow(window)
                    time.sleep(action_delay)
                    
                    # Try to restore window if minimized
                    if win32gui.IsIconic(window):
                        win32gui.ShowWindow(window, win32con.SW_RESTORE)
                        time.sleep(action_delay)
                except Exception as e:
                    print(f"Warning: Could not set window focus: {str(e)}")
                    # Continue anyway, as the window might already be focused
            
            # Perform click using interception.press
            print("Sending mouse click...")
            self.interception.click(x, y, button="left", delay=action_delay)
            
            # Press Enter twice
            print("Pressing Enter twice...")
            for i in range(2):
                print(f"Enter press {i+1}")
                # Press Enter
                print("Sending Enter key down...")
                self.interception.key_down('enter')
                time.sleep(0.1)
                
                # Release Enter
                print("Sending Enter key up...")
                self.interception.key_up('enter')
                time.sleep(action_delay)
                
            # Wait for flame animation
            print("Waiting for flame animation...")
            time.sleep(parse_delay)
            
            # Take screenshot and parse results
            try:
                print("Taking screenshot...")
                # Get the MapleStory window
                window = self.controller.window_manager.get_window("MapleStory")
                if not window:
                    print("Could not find MapleStory window")
                    return
                    
                # Get the window rectangle
                window_rect = self.controller.window_manager.get_window_rect(window)
                if not window_rect or 'client' not in window_rect:
                    print("Could not get window dimensions")
                    return
                    
                client_rect = window_rect['client']
                width = client_rect[2] - client_rect[0]
                height = client_rect[3] - client_rect[1]
                
                # Get the region coordinates
                left = float(self.left_var.get())
                top = float(self.top_var.get())
                right = float(self.right_var.get())
                bottom = float(self.bottom_var.get())
                
                # Convert relative coordinates to absolute
                region = {
                    'left': client_rect[0] + int(left * width),
                    'top': client_rect[1] + int(top * height),
                    'right': client_rect[0] + int(right * width),
                    'bottom': client_rect[1] + int(bottom * height)
                }
                
                print(f"Capture region: {region}")
                
                # Take screenshot
                with mss.mss() as sct:
                    monitor = {
                        'left': region['left'],
                        'top': region['top'],
                        'width': region['right'] - region['left'],
                        'height': region['bottom'] - region['top']
                    }
                    print(f"Taking screenshot with monitor settings: {monitor}")
                    screenshot = sct.grab(monitor)
                    image = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                    
                    # Save the screenshot
                    base_dir = "results/flames"
                    today = datetime.now().strftime("%Y-%m-%d")
                    save_dir = os.path.join(base_dir, today)
                    os.makedirs(save_dir, exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%H-%M-%S")
                    filename = f"flame_{timestamp}.png"
                    filepath = os.path.join(save_dir, filename)
                    image.save(filepath)
                    print(f"Screenshot saved to: {filepath}")
                    
                    # Parse results
                    print("Parsing results...")
                    results = self.controller.flame_processor.parse_flame_results(image)
                    
                    # Print the results
                    if results and 'stats' in results:
                        print("\nExtracted Stats:")
                        for stat, value in results['stats'].items():
                            print(f"{stat}: {value}")
                        if results.get('attack_increase'):
                            print(f"Attack Increase: {results['attack_increase']}")
                        if results.get('cp_increase'):
                            print(f"CP Increase: {results['cp_increase']}")
                        
                        # Update the results display
                        self._update_results_display(results)
                    else:
                        print("No results available")
                        self._update_results_display(None)
                    
            except Exception as e:
                print(f"Error in screenshot/parsing: {str(e)}")
                import traceback
                traceback.print_exc()
                self._update_results_display(None)
                
        except Exception as e:
            print(f"Error in click sequence: {str(e)}")
            import traceback
            traceback.print_exc()
            self._update_results_display(None)
            
    def _start_keyboard_monitor(self):
        """Start monitoring for keyboard interrupt"""
        self.should_stop = False
        self.keyboard_thread = threading.Thread(target=self._monitor_keyboard)
        self.keyboard_thread.daemon = True  # Thread will exit when main program exits
        self.keyboard_thread.start()
        
    def _monitor_keyboard(self):
        """Monitor for ESC key press using interception-python"""
        try:
            ctx = InterceptionContext()
            ctx.set_filter(lambda d: is_keyboard(d), InterceptionContext.FILTER_KEY_DOWN)

            print("Keyboard monitor started - press ESC to stop.")

            while not self.should_stop:
                device = ctx.wait()
                stroke = ctx.receive(device)

                if isinstance(stroke, KeyCode) and stroke.code == KeyCode.ESC:
                    self.should_stop = True
                    print("\nESC key pressed - stopping roll process...")
                    break

        except Exception as e:
            print(f"Error in keyboard monitoring: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def _animate_button(self):
        """Animate the button while running"""
        if not self.is_animating:
            return
            
        # Toggle between red and black text
        current_style = self.start_button.cget('style')
        new_style = 'Running.TButton' if current_style != 'Running.TButton' else 'Normal.TButton'
        self.start_button.configure(style=new_style)
        
        # Schedule next animation frame
        self.root.after(500, self._animate_button)
        
    def _on_start_clicked(self):
        """Handle start button click"""
        try:
            print("\nStart button clicked")
            
            # Update UI to show running state
            self.start_button.config(text="Running", style='Running.TButton')
            self.status_label.config(text="Rolling flame, press ESC to force stop.")
            self.root.update()  # Force UI update
            
            # Start animation
            self.is_animating = True
            self._animate_button()
            
            # Start keyboard monitoring
            self._start_keyboard_monitor()
            
            # Get the MapleStory window
            window = self.controller.window_manager.get_window("MapleStory")
            if not window:
                print("Could not find MapleStory window")
                messagebox.showerror("Error", "Could not find MapleStory window. Make sure MapleStory is running.")
                return
            
            print(f"Found MapleStory window: {window}")
            
            # Get the window rectangle
            window_rect = self.controller.window_manager.get_window_rect(window)
            if not window_rect:
                print("Could not get window rectangle")
                messagebox.showerror("Error", "Could not get window dimensions")
                return
                
            print(f"Window rectangle: {window_rect}")
            
            # Get the client rectangle for relative coordinates
            if 'client' not in window_rect:
                print("No client rectangle in window info")
                messagebox.showerror("Error", "Could not get client area dimensions")
                return
                
            client_rect = window_rect['client']
            width = client_rect[2] - client_rect[0]
            height = client_rect[3] - client_rect[1]
            
            print(f"Client rectangle: {client_rect}")
            print(f"Client dimensions: {width}x{height}")
            
            # Get the reroll position coordinates
            try:
                x = float(self.x_var.get())
                y = float(self.y_var.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid reroll position coordinates")
                return
                
            # Calculate absolute coordinates
            abs_x = client_rect[0] + int(x * width)
            abs_y = client_rect[1] + int(y * height)
            
            print(f"Moving cursor to: ({abs_x}, {abs_y})")
            
            # Get number of tries
            try:
                tries = int(self.tries_var.get())
                if tries <= 0:
                    messagebox.showerror("Error", "Number of tries must be positive")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid number of tries")
                return
            
            # Get enabled thresholds
            thresholds = {}
            for stat, var in self.threshold_vars.items():
                if var.get():
                    try:
                        value = int(self.threshold_values[stat].get())
                        if value < 0:
                            messagebox.showerror("Error", f"{stat} threshold must be non-negative")
                            return
                        thresholds[stat] = value
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid {stat} threshold value")
                        return
            
            if not thresholds:
                messagebox.showerror("Error", "Please select at least one threshold")
                return
            
            print(f"Starting reroll process with {tries} tries")
            print(f"Thresholds: {thresholds}")
            
            # Perform reroll loop
            for attempt in range(tries):
                # Check if we should stop
                if self.should_stop:
                    print("Roll process stopped by user")
                    self.status_label.config(text="Roll process stopped by user")
                    self.root.update()  # Force UI update
                    return
                    
                print(f"\nAttempt {attempt + 1}/{tries}")
                
                # Perform click sequence and parse results
                self._perform_click_sequence(abs_x, abs_y)
                
                # Check if we should stop after each attempt
                if self.should_stop:
                    print("Roll process stopped by user")
                    self.status_label.config(text="Roll process stopped by user")
                    self.root.update()  # Force UI update
                    return
                
                # Get the results from the results display
                results_text = self.results_text.get(1.0, tk.END).strip()
                if not results_text or results_text == "No results available":
                    print("No results available, continuing...")
                    continue
                
                # Parse the results text to get stats
                stats = {}
                for line in results_text.split('\n'):
                    if ':' in line:
                        # Split only on the first colon
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            stat = parts[0].strip()
                            value_str = parts[1].strip()
                            try:
                                # Extract the first number from the value string
                                import re
                                # Updated regex pattern to handle various formats
                                pattern = r'[+-]?\d+'
                                numbers = re.findall(pattern, value_str)
                                if numbers:
                                    value = int(numbers[0])
                                    stats[stat] = value
                            except ValueError:
                                continue
                    elif 'Stats |' in line or 'All Stats' in line:
                        # Handle both "Stats" and "All Stats" cases
                        try:
                            import re
                            numbers = re.findall(r'[+-]?\d+', line)
                            if numbers:
                                stats['STATS%'] = int(numbers[0])
                        except ValueError:
                            continue
                    else:
                        # Handle cases where stats are in the format "STAT +value" or "STAT +value)"
                        try:
                            import re
                            # Match stat names followed by optional characters and a number
                            stat_pattern = r'(STR|DEX|INT|LUK|STATS?)\s*[^0-9]*([+-]?\d+)'
                            matches = re.findall(stat_pattern, line, re.IGNORECASE)
                            for stat, value in matches:
                                # Normalize stat name
                                stat = stat.upper()
                                if stat == 'STATS':
                                    stat = 'STATS%'
                                stats[stat] = int(value)
                        except ValueError:
                            continue
                
                if not stats:
                    print("Could not parse stats from results, continuing...")
                    continue
                
                # Check if thresholds are met
                thresholds_met = True
                for stat, threshold in thresholds.items():
                    if stat not in stats:
                        print(f"Warning: {stat} not found in results")
                        thresholds_met = False
                        break
                    
                    value = stats[stat]
                    if value < threshold:
                        print(f"{stat} threshold not met: {value} < {threshold}")
                        thresholds_met = False
                        break
                
                if thresholds_met:
                    print("All thresholds met! Stopping reroll process.")
                    self.status_label.config(text="All thresholds met! Stopping reroll process.")
                    self.root.update()  # Force UI update
                    return
                
                print("Thresholds not met, continuing...")
                
                # Update the results display with current attempt info
                self.results_text.config(state=tk.NORMAL)
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(1.0, f"Attempt {attempt + 1}/{tries}\n\n")
                self.results_text.insert(tk.END, results_text)
                self.results_text.config(state=tk.DISABLED)
                self.root.update()  # Force UI update
            
            print("Maximum number of tries reached without meeting thresholds")
            self.status_label.config(text="Maximum number of tries reached without meeting thresholds")
            self.root.update()  # Force UI update
            
        except Exception as e:
            print(f"Error in start button click: {str(e)}")
            import traceback
            traceback.print_exc()
            self.status_label.config(text=f"An error occurred: {str(e)}")
            self.root.update()  # Force UI update
        finally:
            # Reset the stop flag and UI
            self.should_stop = False
            self.is_animating = False
            self.start_button.config(text="Roll", style='Normal.TButton')
            self.root.update()  # Force UI update
        
    def _on_set_position(self):
        """Open the position selector window"""
        try:
            print("Starting position selection...")
            
            # Get the MapleStory window
            window = self.controller.window_manager.get_window("MapleStory")
            if not window:
                print("Could not find MapleStory window")
                messagebox.showerror("Error", "Could not find MapleStory window. Make sure MapleStory is running.")
                return
            
            print(f"Found MapleStory window: {window}")
            
            # Get the window rectangle
            window_rect = self.controller.window_manager.get_window_rect(window)
            if not window_rect:
                print("Could not get window rectangle")
                messagebox.showerror("Error", "Could not get window dimensions")
                return
                
            print(f"Window rectangle: {window_rect}")
            
            # Get the client rectangle for relative coordinates
            if 'client' not in window_rect:
                print("No client rectangle in window info")
                messagebox.showerror("Error", "Could not get client area dimensions")
                return
                
            client_rect = window_rect['client']
            width = client_rect[2] - client_rect[0]
            height = client_rect[3] - client_rect[1]
            
            print(f"Client rectangle: {client_rect}")
            print(f"Client dimensions: {width}x{height}")
            
            def on_position_selected(x, y):
                try:
                    print(f"Position selected: ({x}, {y})")
                    
                    # Convert absolute coordinates to relative
                    rel_x = (x - client_rect[0]) / width
                    rel_y = (y - client_rect[1]) / height
                    
                    print(f"Relative coordinates: x={rel_x}, y={rel_y}")
                    
                    # Update the input fields
                    self.x_var.set(f"{rel_x:.3f}")
                    self.y_var.set(f"{rel_y:.3f}")
                    
                except Exception as e:
                    print(f"Error in position selection callback: {str(e)}")
                    messagebox.showerror("Error", f"Failed to process selected position: {str(e)}")
            
            # Create and run the position selector
            print("Creating position selector...")
            selector = PositionSelector(on_position_selected, window_rect, self.root)  # Added self.root as parent
            print("Running position selector...")
            selector.run()
            
        except Exception as e:
            print(f"Error in position selection: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
    def _on_check_position(self):
        """Move cursor to the specified position"""
        try:
            print("Checking position...")
            
            # Get the MapleStory window
            window = self.controller.window_manager.get_window("MapleStory")
            if not window:
                print("Could not find MapleStory window")
                messagebox.showerror("Error", "Could not find MapleStory window. Make sure MapleStory is running.")
                return
            
            print(f"Found MapleStory window: {window}")
            
            # Get the window rectangle
            window_rect = self.controller.window_manager.get_window_rect(window)
            if not window_rect:
                print("Could not get window rectangle")
                messagebox.showerror("Error", "Could not get window dimensions")
                return
                
            print(f"Window rectangle: {window_rect}")
            
            # Get the client rectangle for relative coordinates
            if 'client' not in window_rect:
                print("No client rectangle in window info")
                messagebox.showerror("Error", "Could not get client area dimensions")
                return
                
            client_rect = window_rect['client']
            width = client_rect[2] - client_rect[0]
            height = client_rect[3] - client_rect[1]
            
            print(f"Client rectangle: {client_rect}")
            print(f"Client dimensions: {width}x{height}")
            
            # Get the position coordinates from the input fields
            try:
                x = float(self.x_var.get())
                y = float(self.y_var.get())
            except ValueError:
                print("Invalid position coordinates")
                messagebox.showerror("Error", "Invalid position coordinates")
                return
                
            # Convert relative coordinates to absolute
            abs_x = client_rect[0] + int(x * width)
            abs_y = client_rect[1] + int(y * height)
            
            print(f"Moving cursor to: ({abs_x}, {abs_y})")
            
            # Move the cursor
            current_x, current_y = win32api.GetCursorPos()
            self._move_cursor_smoothly(current_x, current_y, abs_x, abs_y, steps=10, delay=0.05)
            
        except Exception as e:
            print(f"Error checking position: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
    def _create_region_adjustment(self):
        """Create controls for adjusting the capture region"""
        # Region adjustment frame
        region_frame = ttk.LabelFrame(self.main_frame, text="Capture Region Adjustment", padding="5")
        region_frame.grid(row=2, column=0, sticky=tk.EW, pady=5)
        
        # Left adjustment
        ttk.Label(region_frame, text="Left:").grid(row=0, column=0, padx=2)
        self.left_var = tk.StringVar(value="0.44")
        ttk.Entry(region_frame, textvariable=self.left_var, width=5).grid(row=0, column=1, padx=2)
        
        # Top adjustment
        ttk.Label(region_frame, text="Top:").grid(row=0, column=2, padx=2)
        self.top_var = tk.StringVar(value="0.5")
        ttk.Entry(region_frame, textvariable=self.top_var, width=5).grid(row=0, column=3, padx=2)
        
        # Right adjustment
        ttk.Label(region_frame, text="Right:").grid(row=0, column=4, padx=2)
        self.right_var = tk.StringVar(value="0.56")
        ttk.Entry(region_frame, textvariable=self.right_var, width=5).grid(row=0, column=5, padx=2)
        
        # Bottom adjustment
        ttk.Label(region_frame, text="Bottom:").grid(row=0, column=6, padx=2)
        self.bottom_var = tk.StringVar(value="0.66")
        ttk.Entry(region_frame, textvariable=self.bottom_var, width=5).grid(row=0, column=7, padx=2)
        
        # Test Screenshot button
        self.test_button = ttk.Button(
            region_frame,
            text="Test Screenshot",
            command=self._on_test_screenshot
        )
        self.test_button.grid(row=1, column=0, columnspan=4, pady=5)
        
        # Select Region button
        self.select_region_button = ttk.Button(
            region_frame,
            text="Select Region",
            command=self._on_select_region
        )
        self.select_region_button.grid(row=1, column=4, columnspan=4, pady=5)
        
        # Reroll position frame
        position_frame = ttk.LabelFrame(self.main_frame, text="Reroll Position", padding="5")
        position_frame.grid(row=3, column=0, sticky=tk.EW, pady=5)
        
        # X position
        ttk.Label(position_frame, text="X:").grid(row=0, column=0, padx=2)
        self.x_var = tk.StringVar(value="0.5")
        ttk.Entry(position_frame, textvariable=self.x_var, width=5).grid(row=0, column=1, padx=2)
        
        # Y position
        ttk.Label(position_frame, text="Y:").grid(row=0, column=2, padx=2)
        self.y_var = tk.StringVar(value="0.5")
        ttk.Entry(position_frame, textvariable=self.y_var, width=5).grid(row=0, column=3, padx=2)
        
        # Set Position button
        self.set_position_button = ttk.Button(
            position_frame,
            text="Set Reroll Position",
            command=self._on_set_position
        )
        self.set_position_button.grid(row=0, column=4, padx=5)
        
        # Check Position button
        self.check_position_button = ttk.Button(
            position_frame,
            text="Check Position",
            command=self._on_check_position
        )
        self.check_position_button.grid(row=0, column=5, padx=5)
        
        # Add some padding at the bottom
        ttk.Label(self.main_frame, text="").grid(row=4, column=0, pady=5)
        
        # Add status label
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.grid(row=12, column=0, pady=5)
        
    def _on_select_region(self):
        """Handle select region button click"""
        try:
            print("Starting region selection...")
            
            # Get the MapleStory window
            window = self.controller.window_manager.get_window("MapleStory")
            if not window:
                print("Could not find MapleStory window")
                messagebox.showerror("Error", "Could not find MapleStory window. Make sure MapleStory is running.")
                return
            
            print(f"Found MapleStory window: {window}")
            
            # Get the window rectangle
            window_rect = self.controller.window_manager.get_window_rect(window)
            if not window_rect:
                print("Could not get window rectangle")
                messagebox.showerror("Error", "Could not get window dimensions")
                return
                
            print(f"Window rectangle: {window_rect}")
            
            # Get the client rectangle for relative coordinates
            if 'client' not in window_rect:
                print("No client rectangle in window info")
                messagebox.showerror("Error", "Could not get client area dimensions")
                return
                
            client_rect = window_rect['client']
            width = client_rect[2] - client_rect[0]
            height = client_rect[3] - client_rect[1]
            
            print(f"Client rectangle: {client_rect}")
            print(f"Client dimensions: {width}x{height}")
            
            def on_region_selected(region):
                try:
                    print(f"Region selected: {region}")
                    
                    # Convert absolute coordinates to relative
                    rel_left = (region['left'] - client_rect[0]) / width
                    rel_top = (region['top'] - client_rect[1]) / height
                    rel_right = (region['right'] - client_rect[0]) / width
                    rel_bottom = (region['bottom'] - client_rect[1]) / height
                    
                    print(f"Relative coordinates: left={rel_left}, top={rel_top}, right={rel_right}, bottom={rel_bottom}")
                    
                    # Update the input fields
                    self.left_var.set(f"{rel_left:.3f}")
                    self.top_var.set(f"{rel_top:.3f}")
                    self.right_var.set(f"{rel_right:.3f}")
                    self.bottom_var.set(f"{rel_bottom:.3f}")
                    
                except Exception as e:
                    print(f"Error in region selection callback: {str(e)}")
                    messagebox.showerror("Error", f"Failed to process selected region: {str(e)}")
            
            # Create and run the region selector
            print("Creating region selector...")
            selector = RegionSelector(on_region_selected, window_rect, self.root)
            print("Running region selector...")
            selector.run()
            
        except Exception as e:
            print(f"Error in region selection: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
    def _update_results_display(self, results):
        """Update the results display with new results"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        
        if results:
            # Format the results text
            text = "Extracted Stats:\n"
            
            # Add each stat with proper formatting
            for stat, value in results['stats'].items():
                if stat == 'STATS%':
                    text += f"All Stats: {value}\n"
                else:
                    text += f"{stat}: {value}\n"
            
            # Add attack and CP increases if present
            if results['attack_increase'] is not None:
                text += f"Attack Increase: {results['attack_increase']}\n"
            if results['cp_increase'] is not None:
                text += f"CP Increase: {results['cp_increase']}\n"
            
            # Add raw OCR text at the bottom
            text += f"\nRaw OCR text:\n{results['raw_text']}"
        else:
            text = "No results available"
            
        self.results_text.insert(1.0, text)
        self.results_text.config(state=tk.DISABLED)
        
    def _on_force_stop(self):
        """Handle force stop button click"""
        if self.is_animating:
            print("Force stopping roll process...")
            self.should_stop = True
            self.status_label.config(text="Force stopping roll process...")
            self.root.update()  # Force UI update
        else:
            print("No roll process running")
        
    def run(self):
        self.root.mainloop()

class PositionSelector:
    def __init__(self, on_position_selected, window_info, parent):
        self.root = tk.Toplevel(parent)
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.attributes('-alpha', 0.3)  # Make window semi-transparent
        self.root.attributes('-topmost', True)  # Keep window on top
        
        # Get client rectangle (just the content area)
        client_rect = window_info['client']
        client_width = client_rect[2] - client_rect[0]
        client_height = client_rect[3] - client_rect[1]
        
        # Position the window over the MapleStory window's client area
        self.root.geometry(f"{client_width}x{client_height}+{client_rect[0]}+{client_rect[1]}")
        
        # Create a canvas that fills the entire window
        self.canvas = tk.Canvas(self.root, cursor="cross", bg='white', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.on_position_selected = on_position_selected
        self.client_rect = client_rect
        
        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.root.bind("<Escape>", self.on_escape)
        
    def on_click(self, event):
        # Convert to absolute screen coordinates
        x = self.client_rect[0] + event.x
        y = self.client_rect[1] + event.y
        
        # Print debug information
        print(f"Clicked position (absolute): ({x}, {y})")
        print(f"Client rect: {self.client_rect}")
        print(f"Canvas coordinates: x={event.x}, y={event.y}")
        
        self.on_position_selected(x, y)
        self.root.destroy()
        
    def on_escape(self, event):
        self.root.destroy()
        
    def run(self):
        self.root.wait_window() 