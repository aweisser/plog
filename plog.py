#!/usr/bin/env python

import os
import time
import requests
import click
from datetime import datetime, timedelta

# Base URL for Personio API
PERSONIO_API_URL = "https://api.personio.de/v1"

# Load environment variables for API key and secret
API_KEY = os.getenv('PERSONIO_API_KEY')
API_SECRET = os.getenv('PERSONIO_API_SECRET')

# File to store timer state (start, end)
TIMER_FILE = 'plog.staging'

def save_timer_state(start, end=''):
    """Save the timer start and end time to a file."""
    with open(TIMER_FILE, 'a') as file:
        file.write(f"{start},{end}\n")

def load_timer_state():
    """Load all timer start and end times from the file."""
    if os.path.exists(TIMER_FILE):
        with open(TIMER_FILE, 'r') as file:
            lines = file.readlines()
            timers = [line.strip().split(',') for line in lines]
            return [(float(start), float(end) if end else None) for start, end in timers]
    return []

def update_timer_state(timer_data):
    """Overwrite the timer state file with the provided timer data."""
    with open(TIMER_FILE, 'w') as file:
        for start, end in timer_data:
            file.write(f"{start},{end}\n")

def delete_timer_state():
    """Delete the timer state file to reset the timer."""
    if os.path.exists(TIMER_FILE):
        os.remove(TIMER_FILE)

def authenticate():
    """Authenticate with the Personio API and return the access token."""
    url = f"{PERSONIO_API_URL}/auth"
    response = requests.post(url, auth=(API_KEY, API_SECRET))
    
    if response.status_code == 200:
        return response.json().get("data").get("token")
    else:
        raise Exception("Authentication failed")

def log_work_to_personio(access_token, date, hours, description):
    """Log work to Personio API."""
    url = f"{PERSONIO_API_URL}/work_hours"
    headers = {
        'Authorization': f"Bearer {access_token}",
        'Content-Type': 'application/json'
    }
    
    payload = {
        "date": date,
        "hours": hours,
        "description": description
    }

    # Display human-readable payload information
    click.echo(f"Sending the following data to Personio API:")
    click.echo(f"Date: {date}")
    click.echo(f"Hours worked: {hours:.2f}")
    click.echo(f"Description: {description}")

    response = requests.post(url, json=payload, headers=headers)
    
    # Display the response in human-readable form
    if response.status_code == 201:
        click.echo(f"Response from Personio API:")
        click.echo(f"Work logged successfully for {hours:.2f} hours on {date}.")
    else:
        click.echo(f"Failed to log work. Response from Personio:")
        click.echo(response.text)

@click.group()
def cli():
    """CLI group for plog."""
    pass

@cli.command()
def start():
    """Start a new work timer, or do nothing if a timer is already running."""
    timers = load_timer_state()

    # Check if the last timer is still running (i.e., no end time)
    if timers and timers[-1][1] is None:
        click.echo("Timer is already running.")
    else:
        timer_start = time.time()
        save_timer_state(timer_start)
        click.echo("New timer started.")

@cli.command()
def stop():
    """Stop the current work timer."""
    timers = load_timer_state()

    # Check if there's an active timer
    if timers and timers[-1][1] is None:
        timer_start = timers[-1][0]
        timer_end = time.time()
        timers[-1] = (timer_start, timer_end)  # Update the last timer with the end time
        update_timer_state(timers)
        click.echo("Timer stopped.")
    else:
        click.echo("No timer is currently running.")

@cli.command()
@click.option('-a', '--all', is_flag=True, help="Show the total duration for all timers.")
def status(all):
    """Check the status of the current timer or show total duration for all timers."""
    timers = load_timer_state()

    if not timers:
        click.echo("No timer started.")
        return

    if all:
        # Sum all timers and show their start and end times
        total_duration = timedelta()
        for i, (timer_start, timer_end) in enumerate(timers, 1):
            start_dt = datetime.fromtimestamp(timer_start).strftime("%Y-%m-%d %H:%M:%S")
            if timer_end is None:
                timer_end = time.time()
                end_dt = "Currently Running"
            else:
                end_dt = datetime.fromtimestamp(timer_end).strftime("%Y-%m-%d %H:%M:%S")
            
            duration = timedelta(seconds=timer_end - timer_start)
            total_duration += duration
            click.echo(f"Timer {i}: Start: {start_dt}, End: {end_dt}, Duration: {duration}")

        click.echo(f"\nTotal time worked: {total_duration}.")
    else:
        # Show the last timer status
        timer_start, timer_end = timers[-1]
        start_dt = datetime.fromtimestamp(timer_start).strftime("%Y-%m-%d %H:%M:%S")
        if timer_end:
            # Timer was stopped, show final duration
            end_dt = datetime.fromtimestamp(timer_end).strftime("%Y-%m-%d %H:%M:%S")
            duration = timedelta(seconds=timer_end - timer_start)
            click.echo(f"Last timer: Start: {start_dt}, End: {end_dt}, Duration: {duration}")
        else:
            # Timer is still running, show current duration
            current_duration = timedelta(seconds=time.time() - timer_start)
            end_dt = "Currently Running"
            click.echo(f"Last timer: Start: {start_dt}, End: {end_dt}, Duration: {current_duration}")

@cli.command()
@click.option('-m', '--message', prompt='Work description', help='Description of the work performed.')
def push(message):
    """Push all work logs to Personio and reset the timer."""
    timers = load_timer_state()
    
    if not timers:
        click.echo("No timers found to push.")
        return
    
    # Authenticate
    try:
        access_token = authenticate()
    except Exception as e:
        click.echo(f"Error: {e}")
        return
    
    # Log each timer session to Personio
    for timer_start, timer_end in timers:
        if timer_end is None:
            timer_end = time.time()  # If timer is still running, stop it now
        
        duration_in_seconds = timer_end - timer_start
        hours_worked = duration_in_seconds / 3600
        date = str(datetime.now().date())
        
        log_work_to_personio(access_token, date, hours_worked, message)
    
    # Clear the timer state after successful push
    delete_timer_state()
    click.echo("All timers pushed and reset.")

@cli.command()
def reset():
    """Reset the timer completely."""
    delete_timer_state()
    click.echo("Timer has been reset.")

if __name__ == "__main__":
    cli()
