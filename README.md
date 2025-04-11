# Flame Reroll Assistant

A Python-based tool to assist with rerolling flames in MapleStory. This tool automates the process of rolling flames and tracking results.

## Features

- Automatic flame rolling with customizable thresholds
- Real-time result tracking and display
- Configurable capture region and reroll position
- Visual feedback during the rolling process

## Requirements

- Python 3.8 or higher
- MapleStory running in windowed mode
- Required Python packages:
  - tkinter
  - pillow
  - pytesseract
  - mss
  - pywin32
  - interception-python

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/flame-reroll.git
cd flame-reroll
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR:
- Download and install Tesseract OCR from [here](https://github.com/UB-Mannheim/tesseract/wiki)
- Add Tesseract to your system PATH

## Usage

1. Run the application:
```bash
python src/main.py
```

2. Configure the settings:
   - Set your desired thresholds for each stat
   - Configure the number of tries
   - Set the capture region and reroll position

3. Click "Roll" to start the process:
   - The button will turn red and show "Running"
   - A status message will appear at the bottom

4. Monitor the results:
   - Results are displayed in real-time
   - The process will stop automatically if thresholds are met

## Configuration

The application saves your settings automatically in `flame_settings.json`. You can:
- Adjust the capture region for better OCR results
- Set custom thresholds for each stat
- Configure the number of tries
- Save and load different configurations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Use at your own risk and in accordance with MapleStory's terms of service. 
