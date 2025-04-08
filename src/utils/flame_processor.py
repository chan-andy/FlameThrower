import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import mss
import numpy as np
import os
from difflib import get_close_matches
from rapidfuzz import fuzz, process
import cv2

class FlameProcessor:
    def __init__(self):
        self.sct = mss.mss()
        
        # Configure Tesseract path
        try:
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
        except Exception as e:
            print(f"Warning: Could not configure Tesseract path: {e}")
            
        # Define known stat names for fuzzy matching
        self.known_stats = [
            'STR', 'DEX', 'INT', 'LUK', 'WA', 'MA', 'All Stats',
            'MaxHP', 'MaxMP', 'DEF', 'SPEED', 'Attack Increase', 'CP Increase'
        ]
        
    def capture_result_region(self, window_rect):
        """Capture the region containing flame results"""
        try:
            print(f"Capturing window region: {window_rect}")
            
            # Extract the window coordinates from the mss format
            if isinstance(window_rect, dict):
                # mss format: {'window': (left, top, right, bottom), 'client': ...}
                left, top, right, bottom = window_rect['window']
                width = right - left
                height = bottom - top
                print(f"Window dimensions: {width}x{height}")
                
                # Create a new rect in the format mss expects
                monitor = {
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height
                }
            else:
                # If it's already in the correct format, use it directly
                monitor = window_rect
                
            # Take a screenshot of the window
            screenshot = self.sct.grab(monitor)
            print(f"Screenshot size: {screenshot.size}")
            
            # Convert to PIL Image
            screenshot = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            print(f"PIL Image size: {screenshot.size}")
            
            # Define a fixed region for the flame results
            # This region should be adjusted based on your game window
            x = width // 4  # Start at 25% of the width
            y = height // 3  # Start at 33% of the height
            region_width = width // 2  # Take 50% of the width
            region_height = height // 3  # Take 33% of the height
            
            print(f"Using fixed region: x={x}, y={y}, width={region_width}, height={region_height}")
            
            # Crop the screenshot to the result region
            result_region = screenshot.crop((x, y, x + region_width, y + region_height))
            print(f"Cropped region size: {result_region.size}")
            
            return result_region
            
        except Exception as e:
            print(f"Error capturing result region: {str(e)}")
            print(f"Window rect: {window_rect}")
            if 'screenshot' in locals():
                print(f"Screenshot size: {screenshot.size if screenshot else 'None'}")
            return None
            
    def _preprocess_image(self, image):
        """Preprocess the image to improve OCR accuracy"""
        # Convert to grayscale
        image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Apply threshold to make text more distinct
        image = image.point(lambda x: 0 if x < 128 else 255)
        
        # Apply slight blur to reduce noise
        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        return image
        
    def _correct_ocr_text(self, text):
        """Correct common OCR mistakes in the text"""
        # Replace common OCR mistakes
        replacements = {
            '5TR': 'STR',
            '5TAT': 'STAT',
            'Increa5e': 'Increase',
            'l': '1',
            'O': '0',
            'o': '0'
        }
        
        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)
            
        # Use fuzzy matching to correct stat names
        words = text.split()
        corrected_words = []
        
        for word in words:
            # If the word looks like a stat name, try to correct it
            if any(char.isupper() for char in word):
                best_match = process.extractOne(word, self.known_stats, scorer=fuzz.ratio)
                if best_match and best_match[1] > 80:  # 80% similarity threshold
                    corrected_words.append(best_match[0])
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
                
        return ' '.join(corrected_words)
        
    def _parse_number(self, text):
        """Parse a number from text, handling OCR mistakes"""
        # Replace common OCR mistakes in numbers
        text = text.replace('l', '1').replace('O', '0').replace('o', '0')
        
        # Extract the first number found
        match = re.search(r'[+-]?\d+', text)
        if match:
            try:
                return int(match.group(0))
            except ValueError:
                return None
        return None
        
    def parse_flame_results(self, image):
        """Parse the flame results from the captured image"""
        if not image:
            return None
            
        try:
            # Preprocess the image
            processed_image = self._preprocess_image(image)
            
            # Use OCR to extract text with better configuration
            text = pytesseract.image_to_string(
                processed_image,
                config='--psm 6 --oem 3'  # Assume uniform block of text, use LSTM
            )
            
            # Clean up and correct the text
            text = self._correct_ocr_text(text)
            
            # Parse currently owned flames
            currently_owned = None
            owned_match = re.search(r'Currently owned:\s*([+-]?\d+)', text)
            if owned_match:
                currently_owned = self._parse_number(owned_match.group(1))
                
            # Parse remaining flames
            remaining_flames = None
            remaining_match = re.search(r'Remaining:\s*([+-]?\d+)', text)
            if remaining_match:
                remaining_flames = self._parse_number(remaining_match.group(1))
                
            # Parse attack increase
            attack_increase = None
            attack_match = re.search(r'Attack Increase:\s*([+-]?\d+)', text)
            if attack_match:
                attack_increase = self._parse_number(attack_match.group(1))
                
            # Parse CP increase
            cp_increase = None
            cp_match = re.search(r'CP Increase:\s*([+-]?\d+)', text)
            if cp_match:
                cp_increase = self._parse_number(cp_match.group(1))
                
            # Parse stat values with improved patterns
            stats = {}
            stat_patterns = {
                'STR': r'STR\s*[+-]?(\d+)',
                'DEX': r'DEX\s*[+-]?(\d+)',
                'INT': r'INT\s*[+-]?(\d+)',
                'LUK': r'LUK\s*[+-]?(\d+)',
                'WA': r'WA\s*[+-]?(\d+)',
                'MA': r'MA\s*[+-]?(\d+)',
                'STATS%': r'All Stats\s*[+-]?(\d+)%',
                'MaxHP': r'MaxHP\s*[+-]?(\d+)',
                'MaxMP': r'MaxMP\s*[+-]?(\d+)',
                'DEF': r'DEF\s*[+-]?(\d+)',
                'SPEED': r'SPEED\s*[+-]?(\d+)'
            }
            
            for stat, pattern in stat_patterns.items():
                match = re.search(pattern, text)
                if match:
                    value = self._parse_number(match.group(1))
                    if value is not None:
                        stats[stat] = value
                        
            return {
                'currently_owned': currently_owned,
                'remaining_flames': remaining_flames,
                'attack_increase': attack_increase,
                'cp_increase': cp_increase,
                'stats': stats,
                'raw_text': text  # Include the raw OCR text for debugging
            }
        except Exception as e:
            print(f"OCR Error: {str(e)}")
            return {
                'currently_owned': None,
                'remaining_flames': None,
                'attack_increase': None,
                'cp_increase': None,
                'stats': {},
                'raw_text': f"OCR Error: {str(e)}"
            } 