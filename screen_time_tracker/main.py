"""
Main module for the Screen Time Tracker application.
"""

import time
import json
import click
from datetime import datetime
import signal
import sys
import os

from .app_tracker import AppTracker
from .data_manager import DataManager

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
