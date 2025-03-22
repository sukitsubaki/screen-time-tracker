"""
Module for managing storage and retrieval of application usage data.
"""

import os
import json
import sqlite3
import platform
from datetime import datetime, timedelta
import pandas as pd

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
        
        if system == "Darwin":  # macOS
            data_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", app_name)
            elif system == "Windows":
            data_dir = os.path.join(os.environ["APPDATA"], app_name)
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
