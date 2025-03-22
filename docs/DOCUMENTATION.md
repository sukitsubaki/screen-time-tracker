# Screen Time Tracker Documentation

## Overview

Screen Time Tracker is a lightweight Python application that helps you monitor and analyze the time you spend using various applications on your computer.

## Installation

### Prerequisites

- Python 3.8 or higher
- Pip package manager

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/sukitsubaki/screen-time-tracker.git
   cd screen-time-tracker
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Important**: Install operating system-specific dependencies:
   - Windows: `pip install pywin32`
   - macOS: `pip install pyobjc`
   - Linux: `pip install python-xlib`

   For macOS users, `pyobjc` is essential for the application to function correctly.

## Usage

### Basic Commands

- Start tracking:
  ```bash
  python run-tracker.py start
  ```

- Generate report:
  ```bash
  python run-tracker.py report --period daily
  ```

- Make the script executable (optional):
  ```bash
  chmod +x run-tracker.py
  ./run-tracker.py start
  ```

### Available Options

- `--period`: Specify report period (`daily`, `weekly`, `monthly`)
- `--format`: Specify output format (`text`, `json`, `csv`)
- `--output`: Specify output file path

### Examples

Display daily report as text:
```bash
python run-tracker.py report --period daily
```

Save weekly report as JSON file:
```bash
python run-tracker.py report --period weekly --format json --output weekly-report.json
```

## Technical Details

### Data Storage

The application stores tracking data in a SQLite database at the following locations:

- Windows: `%APPDATA%\screen-time-tracker\data.db`
- macOS: `~/Library/Application Support/screen-time-tracker/data.db`
- Linux: `~/.local/share/screen-time-tracker/data.db`

### Architecture

The application consists of three main components:

- **App Tracker**: Monitors active applications using operating system-specific APIs
- **Data Manager**: Manages data storage and querying
- **Main Module**: Provides the CLI interface and coordinates application logic

### Implementation Notes

- The consolidated `run-tracker.py` script combines all components into a single file for easier execution without package installation requirements.
- For macOS users, the `pyobjc` package provides the necessary AppKit interfaces to track active applications.
- For Windows users, `pywin32` provides access to the Windows API for window tracking.
- For Linux users, `python-xlib` provides X Window System interface.

### Troubleshooting

- **"AppKit module not installed"**: If you're using macOS and see this error, run `pip install pyobjc` to install the required dependency.
- **"No module named 'screen_time_tracker'"**: Use the `run-tracker.py` script directly instead of trying to run the package with Python's module syntax.
- **Permission denied when running script**: Make the script executable with `chmod +x run-tracker.py`.

### Known Limitations

- The application only captures foreground applications
- Some applications may have truncated or abbreviated names
- Virtual desktops or multiple monitors may affect tracking accuracy
- On macOS, the application requires `pyobjc` which is a relatively large package
