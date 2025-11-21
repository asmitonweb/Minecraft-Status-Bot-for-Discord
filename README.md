# Minecraft Server Status Monitor

A lightweight Python script that monitors your local Minecraft server process and updates a Discord channel with its status (Online/Offline) using a Webhook.

## Features
- **Real-time Monitoring**: Checks if the Minecraft server process (`java.exe`) is running.
- **Discord Integration**: Sends a rich embed message to a Discord Webhook when status changes.
- **Status Persistence**: Remembers the last status to prevent repeated messages on script restart.
- **Message Cleanup**: Automatically deletes the previous status message so your channel stays clean.
- **System Tray Icon**: Runs quietly in the background with a custom tray icon (Grass Block with Gear).
- **Single Instance**: Prevents multiple copies of the script from running simultaneously.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install psutil requests pystray pillow
    ```

2.  **Configure**:
    - Open `minecraft_status_monitor.py`.
    - Replace `YOUR_WEBHOOK_URL_HERE` with your actual Discord Webhook URL.
    - (Optional) Adjust `CHECK_INTERVAL` or `SERVER_NAME`.

3.  **Run**:
    - Double-click `run_monitor.bat` to start.
    - Use `stop_monitor.bat` to stop all running instances.

## Files
- `minecraft_status_monitor.py`: Main script.
- `run_monitor.bat`: Launcher script.
- `stop_monitor.bat`: Cleanup script to kill running instances.
