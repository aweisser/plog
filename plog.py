#!/usr/bin/env python

import click
from datetime import datetime, timedelta
import os
import pyperclip
import requests
import time

# Base URL for PLOG API (which is a gateway to the Personio API).
PLOG_API_URL = os.getenv('PLOG_API_URL')

# User specific API token
PLOG_API_TOKEN = os.getenv('PLOG_API_TOKEN')

# Function key for plog/token endpoint
PLOG_TOKEN_FUNCTION_KEY = os.getenv('PLOG_TOKEN_FUNCTION_KEY')

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

def log_work_to_plog_api(attendances):
    url = f"{PLOG_API_URL}/api/plog/attendances"
    headers = {
        'Authorization': f"Bearer {PLOG_API_TOKEN}",
        'Content-Type': 'application/json',
    }
    
    payload = { "attendances": attendances }

    # Display human-readable payload information
    click.echo(f"Sending the following data to Plog API:")
    click.echo(f"{payload}")

    response = requests.post(url, json=payload, headers=headers)
    
    # Display the response in human-readable form
    if response.status_code == 200:
        click.echo(f"Response from Plog API:")
        click.echo(response.text)
    else:
        click.echo(f"Failed to log work. Response from plog API:")
        click.echo(response.text)

def get_token_from_plog_api(email): 
    url = f"{PLOG_API_URL}/api/plog/token?email={email}"
    headers = {
        'x-functions-key': PLOG_TOKEN_FUNCTION_KEY
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        click.echo(f"Failed to get token. The plog API returns status {response.status_code}")

@click.group()
def cli():
    """Start, stop and push your daily work logs."""
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
@click.option('-m', '--message', default="", help='Description of the work performed.')
def push(message):
    """Push all work logs to Plog API and reset the timer."""
    if not PLOG_API_URL or not PLOG_API_TOKEN:
        click.echo("Please define PLOG_API_URL and PLOG_API_TOKEN env variables and try again!")
        return
    
    timers = load_timer_state()
    
    if not timers:
        click.echo("No timers found to push.")
        return
    
    # Generate Personio API V1 style "attendances" items from timer sessions.
    # https://developer.personio.de/reference/post_company-attendances
    attendances = []
    for timer_start, timer_end in timers:
        if timer_end is None:
            timer_end = time.time()  # If timer is still running, stop it now
        
        start_dt = datetime.fromtimestamp(timer_start)
        end_dt = datetime.fromtimestamp(timer_end)

        if start_dt.date() != end_dt.date():
            raise Exception(f"Error: Start and end date of each worklog entry must be the same. Call 'plog status', to evaluate.")

        attendance = {
            "comment": message,
            "date": start_dt.strftime("%Y-%m-%d"),
            "start_time": start_dt.strftime("%H:%M:%S"),
            "end_time": end_dt.strftime("%H:%M:%S"),
        }

        attendances.append(attendance)

    # Push the data through the Plog API to Personio.
    log_work_to_plog_api(attendances)

    # Clear the timer state after successful push
    delete_timer_state()
    click.echo("All timers pushed and reset.")

@cli.command(hidden=True)
@click.option('-e', '--email', default="", help='Get a personalized token for a Personio user identified by email.')
def token(email):
    """Get personalized plog API token (admin feature)."""
    if PLOG_TOKEN_FUNCTION_KEY is None or PLOG_TOKEN_FUNCTION_KEY == "":
        click.echo("Please set the ENV variable PLOG_TOKEN_FUNCTION_KEY to use this feature.")
        return
    token=get_token_from_plog_api(email)
    if token is not None:
        pyperclip.copy(token)
        click.echo("The token has been copied to the clipboard.")

@cli.command()
def reset():
    """Reset the timer completely."""
    delete_timer_state()
    click.echo("Timer has been reset.")

if __name__ == "__main__":
    cli()
