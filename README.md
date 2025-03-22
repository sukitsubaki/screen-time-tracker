# Screen Time Tracker

A minimalist Python tracker to record the time spent using different applications on your computer.

## Features

- Monitors active applications and records usage time
- Creates daily, weekly, and monthly reports
- Simple command-line interface for easy operation
- Lightweight with minimal dependencies

## Installation

```bash
# Clone repository
git clone https://github.com/sukitsubaki/screen-time-tracker.git
cd screen-time-tracker

# Install core dependencies
pip install -r requirements.txt

# Install OS-specific dependencies
# For macOS:
pip install pyobjc
# For Windows:
pip install pywin32
# For Linux:
pip install python-xlib
```

## Usage

```bash
# Start tracking
python run-tracker.py start

# Generate report
python run-tracker.py report --period daily

# Alternatively, make the script executable first
chmod +x run-tracker.py

# Then run directly
./run-tracker.py start
```

For advanced usage options, check out the [documentation](docs/DOCUMENTATION.md).

## Requirements

- Python 3.8+
- Operating Systems: Windows, macOS, Linux

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
