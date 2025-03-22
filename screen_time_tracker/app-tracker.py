"""
Module for tracking active applications and gathering usage data.
"""

import time
import platform
import psutil
from datetime import datetime

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
        if self.system == "Darwin":  # macOS
            return self._get_active_window_macos()
        elif self.system == "Windows":
            return self._get_active_window_windows()
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
        """Get active window information on macOS."""
        try:
            # This requires pyobjc
            from AppKit import NSWorkspace
            
            active_app = NSWorkspace.sharedWorkspace().activeApplication()
            app_name = active_app['NSApplicationName']
            # Window title is harder to get on macOS without additional permissions
            
            return {"app_name": app_name, "window_title": ""}
        except ImportError:
            print("AppKit module not installed. Install pyobjc for macOS support.")
            return {"app_name": "Unknown", "window_title": "Unknown"}
        except Exception as e:
            print(f"Error getting active window: {e}")
            return {"app_name": "Unknown", "window_title": "Unknown"}
    
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
