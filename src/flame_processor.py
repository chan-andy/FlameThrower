import easyocr
import re
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Optional
import os
import mss

class FlameProcessor:
    def __init__(self):
        self.result_region = {
            'left': 0.3,    # Start at 30% of the width
            'top': 0.4,     # Start at 40% of the height
            'right': 0.7,   # End at 70% of the width
            'bottom': 0.7   # End at 70% of the height
        }
        # Initialize EasyOCR reader
        self.reader = easyocr.Reader(['en'])
        
    def preprocess_image(self, pil_img: Image.Image) -> np.ndarray:
        """Preprocess the image for better OCR results"""
        # Convert PIL Image to OpenCV format
        image_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        # Increase image size
        scale = 3  # Increased from 2 to 3 for better OCR
        image_cv = cv2.resize(image_cv, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Convert to HSV color space
        hsv = cv2.cvtColor(image_cv, cv2.COLOR_BGR2HSV)
        
        # Create a mask for blue text (adjust these ranges if needed)
        lower_blue = np.array([100, 150, 50])
        upper_blue = np.array([140, 255, 255])
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # Save debug images
        cv2.imwrite('debug_input.png', image_cv)
        cv2.imwrite('debug_blue_mask.png', blue_mask)
        
        # Apply the mask to the original image
        blue_text = cv2.bitwise_and(image_cv, image_cv, mask=blue_mask)
        
        # Convert to grayscale
        gray = cv2.cvtColor(blue_text, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Save more debug images
        cv2.imwrite('debug_blue_text.png', blue_text)
        cv2.imwrite('debug_thresh.png', thresh)
        
        return thresh
        
    def extract_text(self, pil_img: Image.Image) -> str:
        """Extract text from the image using EasyOCR"""
        # Preprocess image
        image = self.preprocess_image(pil_img)
        
        # Get OCR results
        results = self.reader.readtext(image)
        
        # Combine all detected text blocks
        text = ' '.join([result[1] for result in results])
        
        # Print debug info
        print("EasyOCR detected text:")
        print(text)
        print("\nDetailed results:")
        for result in results:
            bbox, text, confidence = result
            print(f"Text: {text}, Confidence: {confidence:.2f}")
            
        return text
        
    def parse_flame_stats(self, text: str) -> Dict:
        """Parse the OCR text to extract flame stats"""
        results = {
            'currently_owned': None,
            'attack_increase': None,
            'cp_increase': None,
            'stats': {},
            'raw_text': text
        }
        
        # Print raw text for debugging
        print("Raw OCR text:", text)
        
        # Store original text for debugging
        original_text = text
        print("Original text:", original_text)
        
        # Basic cleanup - normalize spaces and handle signs
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        
        print("Cleaned text:", text)
        
        # Define stat patterns - handle various spacing and formatting
        stat_patterns = {
            'STR': r'STR\s*[+:]?\s*(\d+)',
            'DEX': r'DEX\s*[+:]?\s*(\d+)',
            'INT': r'INT\s*[+:]?\s*(\d+)',
            'LUK': r'LUK\s*[+:]?\s*(\d+)',
            'MaxHP': r'MaxHP\s*[+:]?\s*(\d+)',
            'DEF': r'DEF\s*[+:]?\s*(\d+)',
            'STATS%': r'(?:All|A11|A1l|Al1)\s*Stats?\s*[+:]?\s*(\d+)',
        }
        
        # Extract stats with debug info
        for key, pattern in stat_patterns.items():
            print(f"\nTrying to match {key} with pattern: {pattern}")
            # Try both in cleaned text and original text
            for current_text in [text, original_text]:
                print(f"Checking text: {current_text}")
                matches = list(re.finditer(pattern, current_text, re.IGNORECASE))
                if matches:
                    for match in matches:
                        try:
                            value = int(match.group(1))
                            # Add % symbol for All Stats
                            if key == 'STATS%':
                                results['stats'][key] = f"{value}%"
                            else:
                                results['stats'][key] = value
                            print(f"Found {key}: {value} (matched text: '{match.group(0)}', full match groups: {match.groups()})")
                            break  # Found a valid match, no need to check original text
                        except ValueError:
                            print(f"Failed to parse value for {key}: {match.group(1)} (matched text: '{match.group(0)}')")
                            continue
            
            if key not in results['stats']:
                print(f"No matches found for {key} pattern: {pattern}")
                # Show context around the stat name if it exists
                for current_text in [text, original_text]:
                    search_text = 'All Stats' if key == 'STATS%' else key
                    if search_text in current_text:
                        start = max(0, current_text.find(search_text) - 15)
                        end = min(len(current_text), current_text.find(search_text) + len(search_text) + 15)
                        print(f"Context around {key} in {'cleaned' if current_text == text else 'original'} text: '{current_text[start:end]}'")
        
        # Extract attack increase and CP increase after stat parsing
        attack_match = re.search(r'Attack\s*Increase\s*:\s*(-\d+)', text)
        if attack_match:
            results['attack_increase'] = int(attack_match.group(1))
            print(f"Found attack increase: {results['attack_increase']}")
            
        cp_match = re.search(r'CP\s*Increase\s*:\s*(-\d+)', text)
        if cp_match:
            results['cp_increase'] = int(cp_match.group(1))
            print(f"Found CP increase: {results['cp_increase']}")
        
        # Print final parsed results
        print("\nFinal parsed results:")
        print("Stats:", results['stats'])
        print("Attack Increase:", results['attack_increase'])
        print("CP Increase:", results['cp_increase'])
        
        return results
        
    def parse_flame_results(self, image: Image.Image) -> Optional[Dict]:
        """Process the flame result image and return parsed stats"""
        try:
            # Extract text from image
            ocr_text = self.extract_text(image)
            
            # Parse the extracted text
            results = self.parse_flame_stats(ocr_text)
            
            # Print the final results
            print("\nFinal parsed results:")
            print("Stats:", results['stats'])
            print("Attack Increase:", results['attack_increase'])
            print("CP Increase:", results['cp_increase'])
            
            return results
            
        except Exception as e:
            print(f"Error parsing flame results: {str(e)}")
            return None 

    def process_flame_results(self, window_info):
        """Process the flame results from the window"""
        try:
            print("\nProcessing flame results...")
            
            # Capture the result region
            print("Capturing result region...")
            result_image = self.capture_result_region(window_info)
            if not result_image:
                print("Failed to capture result region")
                return None
            print(f"Captured image size: {result_image.size}")
            
            # Extract text from the image
            print("Extracting text from image...")
            text = self.extract_text(result_image)
            print(f"Extracted text: {text}")
            
            # Parse the flame stats
            print("Parsing flame stats...")
            stats = self.parse_flame_stats(text)
            print(f"Parsed stats: {stats}")
            
            return stats
            
        except Exception as e:
            print(f"Error processing flame results: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
            
    def capture_result_region(self, window_info):
        """Capture the region containing flame results"""
        try:
            print(f"Capturing window region: {window_info}")
            
            # Extract the window coordinates from the mss format
            if isinstance(window_info, dict):
                # mss format: {'window': (left, top, right, bottom), 'client': ...}
                left, top, right, bottom = window_info['window']
                width = right - left
                height = bottom - top
                print(f"Window dimensions: {width}x{height}")
                
                # Calculate the region coordinates based on relative values
                region_left = left + int(self.result_region['left'] * width)
                region_top = top + int(self.result_region['top'] * height)
                region_right = left + int(self.result_region['right'] * width)
                region_bottom = top + int(self.result_region['bottom'] * height)
                
                # Create a new rect in the format mss expects
                monitor = {
                    "left": region_left,
                    "top": region_top,
                    "width": region_right - region_left,
                    "height": region_bottom - region_top
                }
            else:
                # If it's already in the correct format, use it directly
                monitor = window_info
                
            print(f"Capture region: {monitor}")
            
            # Take a screenshot of the window
            with mss.mss() as sct:
                screenshot = sct.grab(monitor)
                print(f"Screenshot size: {screenshot.size}")
                
                # Convert to PIL Image
                image = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                print(f"PIL Image size: {image.size}")
                
                return image
                
        except Exception as e:
            print(f"Error capturing result region: {str(e)}")
            print(f"Window info: {window_info}")
            if 'screenshot' in locals():
                print(f"Screenshot size: {screenshot.size if screenshot else 'None'}")
            return None 