#!/usr/bin/env python3
"""
Direct launcher for Screen Time Tracker that imports modules directly.
"""

import os
import sys
import time
import json
import click
from datetime import datetime
import signal
import sqlite3
import platform
import psutil
from datetime import timedelta
import pandas as pd

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Class definitions directly imported from original files
# AppTracker class
class AppTracker:
    """Tracks active application usage time."""
    
    def __init__(self):
        """Initialize the app tracker."""
        self.current_app = None
        self.start_time = None
        self.system = platform.system()
    
    def get_active_window_info(self):
        """
        Get information about the currently active window.
        
        Returns:
            dict: Information about the active window including app name and window title.
        """
        if self.system == "Windows":
            return self._get_active_window_windows()
        elif self.system == "Darwin":  # macOS
            return self._get_active_window_macos()
        elif self.system == "Linux":
            return self._get_active_window_linux()
        else:
            return {"app_name": "Unknown", "window_title": "Unknown"}
    
    def _get_active_window_windows(self):
        """Get active window information on Windows."""
        try:
            import win32gui
            import win32process
            
            window = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(window)
            app_name = psutil.Process(pid).name()
            window_title = win32gui.GetWindowText(window)
            
            return {"app_name": app_name, "window_title": window_title}
        except ImportError:
            print("win32gui module not installed. Install pywin32 for Windows support.")
            return {"app_name": "Unknown", "window_title": "Unknown"}
        except Exception as e:
            print(f"Error getting active window: {e}")
            return {"app_name": "Unknown", "window_title": "Unknown"}
    
    def _get_active_window_macos(self):
        """Get active window information on macOS using multiple methods."""
        app_name = "Unknown"
        debug_info = []
        
        # Method 1: Try using psutil to find the process with the highest CPU usage
        # This is a simple heuristic that often works for the active application
        try:
            import psutil
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    # Update CPU percent value
                    proc.cpu_percent(interval=0.1)
                    processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU percent (higher first)
            processes.sort(key=lambda p: p.info['cpu_percent'], reverse=True)
            
            # Filter out system processes and get the first user process
            user_processes = [p for p in processes if p.info['name'] 
                             not in ['kernel_task', 'launchd', 'WindowServer', 'mds', 'mds_stores']]
            
            if user_processes:
                top_process = user_processes[0]
                app_name = top_process.info['name']
                if app_name.endswith('.app'):
                    app_name = app_name[:-4]
                debug_info.append(f"psutil detected: {app_name} (CPU: {top_process.info['cpu_percent']}%)")
        except Exception as e:
            debug_info.append(f"psutil detection failed: {e}")
        
        # Method 2: Try AppleScript (requires accessibility permissions)
        if app_name == "Unknown":
            try:
                import subprocess
                apple_script = 'tell application "System Events" to get name of first application process whose frontmost is true'
                result = subprocess.run(['osascript', '-e', apple_script], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    app_name = result.stdout.strip()
                    debug_info.append(f"AppleScript detected: {app_name}")
                else:
                    debug_info.append(f"AppleScript failed: {result.stderr.strip()}")
            except Exception as e:
                debug_info.append(f"AppleScript error: {e}")
        
        # Method 3: NSWorkspace (requires pyobjc)
        if app_name == "Unknown":
            try:
                from AppKit import NSWorkspace
                active_app = NSWorkspace.sharedWorkspace().activeApplication()
                if active_app and 'NSApplicationName' in active_app:
                    app_name = active_app['NSApplicationName']
                    debug_info.append(f"NSWorkspace detected: {app_name}")
                else:
                    debug_info.append(f"NSWorkspace info incomplete: {active_app}")
            except Exception as e:
                debug_info.append(f"NSWorkspace error: {e}")
        
        # Print debug information
        debug_str = " | ".join(debug_info)
        print(f"App detection methods: {debug_str}")
        
        return {"app_name": app_name, "window_title": ""}
    
    def _get_active_window_linux(self):
        """Get active window information on Linux."""
        try:
            # This requires python-xlib
            from Xlib import display
            
            display_obj = display.Display()
            window = display_obj.get_input_focus().focus
            wmname = window.get_wm_name()
            wmclass = window.get_wm_class()
            
            if wmclass:
                app_name = wmclass[1]
            else:
                app_name = "Unknown"
                
            window_title = wmname if wmname else "Unknown"
            
            return {"app_name": app_name, "window_title": window_title}
        except ImportError:
            print("Xlib module not installed. Install python-xlib for Linux support.")
            return {"app_name": "Unknown", "window_title": "Unknown"}
        except Exception as e:
            print(f"Error getting active window: {e}")
            return {"app_name": "Unknown", "window_title": "Unknown"}
    
    def start_tracking(self):
        """Start tracking the currently active application."""
        active_window = self.get_active_window_info()
        self.current_app = active_window["app_name"]
        self.start_time = datetime.now()
        return self.current_app
    
    def stop_tracking(self):
        """
        Stop tracking the current application and calculate usage time.
        
        Returns:
            dict: Information about the tracked session including app name, 
                  start time, end time, and duration in seconds.
        """
        if not self.current_app or not self.start_time:
            return None
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        session_data = {
            "app_name": self.current_app,
            "start_time": self.start_time,
            "end_time": end_time,
            "duration": duration
        }
        
        self.current_app = None
        self.start_time = None
        
        return session_data

# DataManager class
class DataManager:
    """Manages the storage and retrieval of application usage data."""
    
    def __init__(self):
        """Initialize the data manager and set up the database."""
        self.db_path = self._get_data_path()
        self._initialize_database()
    
    def _get_data_path(self):
        """
        Get the appropriate path for storing application data based on the operating system.
        
        Returns:
            str: Path to the database file.
        """
        app_name = "screen-time-tracker"
        system = platform.system()
        
        if system == "Windows":
            data_dir = os.path.join(os.environ["APPDATA"], app_name)
        elif system == "Darwin":  # macOS
            data_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", app_name)
        else:  # Linux and others
            data_dir = os.path.join(os.path.expanduser("~"), ".local", "share", app_name)
        
        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        return os.path.join(data_dir, "data.db")
    
    def _initialize_database(self):
        """Initialize the SQLite database and create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            duration REAL NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_session(self, session_data):
        """
        Save a session to the database.
        
        Args:
            session_data (dict): Session data including app_name, start_time, end_time, and duration.
            
        Returns:
            int: ID of the inserted record.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO sessions (app_name, start_time, end_time, duration)
        VALUES (?, ?, ?, ?)
        ''', (
            session_data["app_name"],
            session_data["start_time"].isoformat(),
            session_data["end_time"].isoformat(),
            session_data["duration"]
        ))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_id
    
    def get_sessions(self, days=1):
        """
        Retrieve sessions from the specified number of past days.
        
        Args:
            days (int): Number of days to look back.
            
        Returns:
            pandas.DataFrame: DataFrame containing the session data.
        """
        conn = sqlite3.connect(self.db_path)
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = f'''
        SELECT * FROM sessions
        WHERE start_time >= ?
        ORDER BY start_time DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=(start_date,))
        
        # Convert timestamp strings to datetime objects
        df["start_time"] = pd.to_datetime(df["start_time"])
        df["end_time"] = pd.to_datetime(df["end_time"])
        
        conn.close()
        
        return df
    
    def generate_report(self, period="daily"):
        """
        Generate a usage report for the specified period.
        
        Args:
            period (str): Period type - "daily", "weekly", or "monthly".
            
        Returns:
            dict: Report data with app usage statistics.
        """
        days_lookup = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30
        }
        
        days = days_lookup.get(period, 1)
        sessions = self.get_sessions(days=days)
        
        if sessions.empty:
            return {"error": "No data found for the specified period"}
        
        # Group by app and calculate total duration
        app_usage = sessions.groupby("app_name")["duration"].sum().reset_index()
        app_usage = app_usage.sort_values("duration", ascending=False)
        
        # Calculate percentages
        total_duration = app_usage["duration"].sum()
        app_usage["percentage"] = (app_usage["duration"] / total_duration * 100).round(2)
        
        # Format durations as hours, minutes, seconds
        app_usage["formatted_duration"] = app_usage["duration"].apply(
            lambda x: f"{int(x // 3600)}h {int((x % 3600) // 60)}m {int(x % 60)}s"
        )
        
        # Create the report
        report = {
            "period": period,
            "start_date": sessions["start_time"].min().strftime("%Y-%m-%d"),
            "end_date": sessions["end_time"].max().strftime("%Y-%m-%d"),
            "total_duration": f"{int(total_duration // 3600)}h {int((total_duration % 3600) // 60)}m {int(total_duration % 60)}s",
            "app_usage": app_usage.to_dict("records")
        }
        
        return report

# Global variables for tracking
tracker = None
data_manager = None
running = False

def signal_handler(sig, frame):
    """Handle exit signals and stop tracking gracefully."""
    global running
    print("\nStopping screen time tracker...")
    running = False
    sys.exit(0)

def start_tracking_loop():
    """Start the continuous tracking loop."""
    global tracker, data_manager, running
    
    tracker = AppTracker()
    data_manager = DataManager()
    running = True
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Screen time tracker started. Press Ctrl+C to stop.")
    
    last_app = None
    session_data = None
    
    try:
        while running:
            current_app_info = tracker.get_active_window_info()
            current_app = current_app_info["app_name"]
            
            if current_app != last_app:
                # If we were tracking an app, save that session
                if session_data:
                    session_data = tracker.stop_tracking()
                    data_manager.save_session(session_data)
                    print(f"Saved session: {session_data['app_name']} - {int(session_data['duration'])} seconds")
                
                # Start tracking the new app
                tracker.start_tracking()
                last_app = current_app
                print(f"Now tracking: {current_app}")
            
            # Sleep for a bit to avoid excessive CPU usage
            time.sleep(1)
    
    except Exception as e:
        print(f"Error in tracking loop: {e}")
    finally:
        # If we were tracking an app, save that final session
        if tracker.current_app:
            session_data = tracker.stop_tracking()
            if session_data:
                data_manager.save_session(session_data)
                print(f"Saved final session: {session_data['app_name']} - {int(session_data['duration'])} seconds")

@click.group()
def cli():
    """Screen Time Tracker - Monitor your application usage."""
    pass

@cli.command()
def start():
    """Start tracking screen time."""
    start_tracking_loop()

@cli.command()
@click.option('--period', type=click.Choice(['daily', 'weekly', 'monthly']), default='daily', 
              help='Period for the report (daily, weekly, or monthly)')
@click.option('--format', type=click.Choice(['text', 'json', 'csv']), default='text',
              help='Output format (text, json, or csv)')
@click.option('--output', type=click.Path(), help='Output file path')
def report(period, format, output):
    """Generate a screen time report."""
    data_manager = DataManager()
    report_data = data_manager.generate_report(period)
    
    if "error" in report_data:
        click.echo(f"Error: {report_data['error']}")
        return
    
    if format == 'text':
        click.echo(f"\n=== {period.capitalize()} Screen Time Report ===")
        click.echo(f"Period: {report_data['start_date']} to {report_data['end_date']}")
        click.echo(f"Total time tracked: {report_data['total_duration']}")
        click.echo("\nApplication Usage:")
        
        for app in report_data['app_usage']:
            click.echo(f"  {app['app_name']}: {app['formatted_duration']} ({app['percentage']}%)")
    
    elif format == 'json':
        json_data = json.dumps(report_data, indent=2)
        if output:
            with open(output, 'w') as f:
                f.write(json_data)
            click.echo(f"Report saved to {output}")
        else:
            click.echo(json_data)
    
    elif format == 'csv':
        import pandas as pd
        df = pd.DataFrame(report_data['app_usage'])
        if output:
            df.to_csv(output, index=False)
            click.echo(f"Report saved to {output}")
        else:
            click.echo(df.to_csv(index=False))

if __name__ == "__main__":
    cli()
