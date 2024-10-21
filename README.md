
# Plog - Command Line Tool for Logging Work with Personio

`plog` is a simple CLI tool written in Python that helps track work hours and logs them to Personio. It provides commands for starting and stopping a timer, checking the status (with human-readable start and end times), manually logging work hours, and pushing the logged hours to Personio's API.

## Features

- **Start/Stop Timer**: Start and stop a work timer, and keep track of hours worked.
- **Manual Time Entry**: If you forget to stop the timer, you can manually specify hours worked.
- **Push Work Logs**: Push the tracked hours to the Personio API with a description of the work done.
- **Idempotent Start/Stop**: Running `start` or `stop` multiple times will have no effect if the timer is already running or stopped.
- **Reset Timer**: Easily reset the timer to clear any ongoing or finished session.
- **Human-Readable Status**: The `status` command displays timers with human-readable start and end dates.

## Prerequisites

Before using `plog`, ensure you have the following installed:

- **Python 3.6 or higher**
- **Pip** (Python package manager)

Additionally, make sure you have your **Personio API credentials** (API key and secret). You'll need to set these as environment variables to authenticate with the Personio API.

## Installation

### 1. Clone the Repository

First, clone the repository to your local machine:

```bash
git clone https://github.com/yourusername/plog.git
cd plog
```

### 2. Install Required Dependencies

Install the necessary Python packages:

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt` file, you can install the required packages individually:

```bash
pip install requests click
```

### 3. Make the Script Executable

Make sure the `plog.py` script is executable:

```bash
chmod +x plog.py
```

Optionally, move the script to a directory included in your `PATH` so you can run `plog` from anywhere:

```bash
sudo mv plog.py /usr/local/bin/plog
```

## Environment Variables

Before using `plog`, you need to configure your Personio API credentials as environment variables. This will allow the tool to authenticate with the Personio API.

Add the following lines to your shell configuration file (e.g., `.bashrc`, `.zshrc`, or equivalent):

```bash
export PERSONIO_API_KEY='your_personio_api_key'
export PERSONIO_API_SECRET='your_personio_api_secret'
```

After updating the file, reload your shell configuration:

```bash
source ~/.bashrc  # or ~/.zshrc
```

## Usage

Once installed, you can use the `plog` tool to manage your work sessions and log them to Personio.

### 1. Start Timer

Start a work session timer:

```bash
plog start
```

If the timer is already running, `plog` will inform you:

```bash
$ plog start
Timer is already running.
```

### 2. Stop Timer

Stop the current work session:

```bash
plog stop
```

If the timer has already been stopped, `plog` will inform you:

```bash
$ plog stop
Timer is already stopped.
```

### 3. Check Timer Status

You can check the status of the timer to see whether it is running or stopped, and how long it has been running:

```bash
plog status
```

Example output when the timer is running:

```bash
Last timer: Start: 2024-10-21 09:30:45, End: Currently Running, Duration: 1 hour, 45 minutes, and 15 seconds.
```

Example output when the last timer is stopped:

```bash
Last timer: Start: 2024-10-20 14:15:00, End: 2024-10-20 16:30:20, Duration: 2 hours, 15 minutes, and 20 seconds.
```

### 4. Check Total Time for All Timers

You can also check the total duration for all timers (completed or running) with the `--all` option:

```bash
plog status --all
```

Example output:

```bash
Timer 1: Start: 2024-10-20 09:15:00, End: 2024-10-20 11:15:00, Duration: 2:00:00
Timer 2: Start: 2024-10-21 09:30:45, End: Currently Running, Duration: 1:45:15

Total time worked: 3 hours, 45 minutes, and 15 seconds.
```

### 5. Push Hours to Personio

After you’ve finished working, you can push the logged hours to Personio. Provide a description of the work you’ve done using the `-m` (message) flag.

#### Push Using Timer

```bash
plog push -m "Worked on project X"
```

This will log the hours tracked by the timer to Personio.

#### Push with Manual Time

If you forgot to stop the timer or want to manually specify the hours worked, use the `-t` flag to set the hours explicitly:

```bash
plog push -m "Worked on project X" -t 4.5
```

This will log 4.5 hours of work to Personio, regardless of the timer.

### 6. Reset the Timer

If you want to completely reset the timer (whether running or stopped), use the `reset` command:

```bash
plog reset
```

This will delete the timer state and reset it for future sessions.

## Example Session

Here’s an example of how you might use `plog` in a typical work session:

1. **Start the timer** when you begin working:
   
   ```bash
   plog start
   ```

2. **Work on your task**. Once done, stop the timer:

   ```bash
   plog stop
   ```

3. **Check the status** (optional) to see how much time was logged:

   ```bash
   plog status
   ```

4. **Push the hours** to Personio with a description of the work:

   ```bash
   plog push -m "Completed tasks for project X"
   ```

5. **Reset the timer** (optional):

   ```bash
   plog reset
   ```

## Idempotent Commands

- **Start (`plog start`)**: If the timer is already running, this command will not reset or restart the timer.
- **Stop (`plog stop`)**: If the timer has already been stopped, this command will not affect the timer again.
- **Reset (`plog reset`)**: This command will clear the timer state, whether the timer is running or stopped.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
