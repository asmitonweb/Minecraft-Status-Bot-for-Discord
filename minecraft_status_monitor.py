import psutil
import psutil
import os
import json
import requests
import time
import threading
from datetime import datetime
import pystray
from PIL import Image, ImageDraw

# Configuration
DISCORD_WEBHOOK_URL = "YOUR_WEBHOOK_URL_HERE"
MINECRAFT_PROCESS_NAME = "java.exe"
CHECK_INTERVAL = 60
SERVER_NAME = "Closed Room Inc. Minecraft Server"

STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".server_status")

def load_previous_state():
    try:
        with open(STATUS_FILE, "r") as f:
            content = f.read().strip()
            try:
                # Try parsing as JSON
                return json.loads(content)
            except json.JSONDecodeError:
                # Fallback for legacy plain text file
                return {"status": content, "message_id": None}
    except FileNotFoundError:
        return {"status": None, "message_id": None}

def save_current_state(status, message_id):
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump({"status": status, "message_id": message_id}, f)
    except Exception as e:
        print(f"Failed to save status: {e}")

current_state = load_previous_state()
previous_status = current_state["status"]
last_message_id = current_state["message_id"]
running = True

def is_minecraft_running():
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] and MINECRAFT_PROCESS_NAME.lower() in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and any('minecraft' in str(arg).lower() or 'server.jar' in str(arg).lower() for arg in cmdline):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def send_discord_update(status):
    global previous_status, last_message_id
    if status == previous_status:
        return
    
    # Delete previous message if it exists
    if last_message_id:
        try:
            delete_url = f"{DISCORD_WEBHOOK_URL}/messages/{last_message_id}"
            requests.delete(delete_url)
            print(f"Deleted old message: {last_message_id}")
        except Exception as e:
            print(f"Failed to delete old message: {e}")

    embed = {
        "title": f"{'🟢' if status == 'online' else '🔴'} {SERVER_NAME}",
        "description": f"Server is **{status.upper()}**",
        "color": 65280 if status == 'online' else 16711680,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        # Add ?wait=true to get the message object back
        response = requests.post(f"{DISCORD_WEBHOOK_URL}?wait=true", json={"embeds": [embed]})
        response.raise_for_status()
        message_data = response.json()
        new_message_id = message_data.get("id")
        
        previous_status = status
        last_message_id = new_message_id
        save_current_state(status, new_message_id)
        
        print(f"Discord updated: Server {status}, Message ID: {new_message_id}")
    except Exception as e:
        print(f"Failed to send Discord update: {e}")

def monitor_loop(icon):
    global running
    icon.visible = True
    while running:
        is_running = is_minecraft_running()
        status = "online" if is_running else "offline"
        send_discord_update(status)
        
        # Update icon tooltip or state if needed
        icon.title = f"{SERVER_NAME}: {status.upper()}"
        
        time.sleep(CHECK_INTERVAL)

def create_minecraft_icon():
    # Create a 64x64 image
    width, height = 64, 64
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Colors
    grass_color = (94, 157, 52)
    dirt_color = (139, 69, 19)
    side_grass_color = (60, 100, 30) # Darker green for side
    
    # Draw the block (simple 2D side view for clarity in small tray)
    # Top 1/3 is grass
    draw.rectangle((0, 0, width, height // 3), fill=grass_color)
    
    # Bottom 2/3 is dirt
    draw.rectangle((0, height // 3, width, height), fill=dirt_color)
    
    # Add some "grass hanging down" pixels
    for x in range(0, width, 8):
        draw.rectangle((x, height // 3, x + 4, height // 3 + 4), fill=grass_color)
        
    # Add some noise/texture to dirt
    import random
    for _ in range(50):
        x = random.randint(0, width-1)
        y = random.randint(height // 3, height-1)
        draw.point((x, y), fill=(100, 50, 10))

    # Draw a gear overlay (simple representation)
    gear_color = (150, 150, 150)
    center_x, center_y = width - 20, height - 20
    radius = 12
    
    # Draw gear teeth (8 teeth)
    import math
    for i in range(8):
        angle = i * (360 / 8)
        rad = math.radians(angle)
        x1 = center_x + (radius + 4) * math.cos(rad)
        y1 = center_y + (radius + 4) * math.sin(rad)
        x2 = center_x + (radius - 2) * math.cos(rad)
        y2 = center_y + (radius - 2) * math.sin(rad)
        draw.line((x1, y1, x2, y2), fill=gear_color, width=5)

    # Draw gear body
    draw.ellipse((center_x - radius, center_y - radius, center_x + radius, center_y + radius), fill=gear_color)
    
    # Draw center hole
    hole_color = (50, 50, 50)
    draw.ellipse((center_x - 4, center_y - 4, center_x + 4, center_y + 4), fill=hole_color)

    return image

def quit_action(icon, item):
    global running
    running = False
    icon.stop()

def main():
    # Create the icon
    image = create_minecraft_icon()
    menu = pystray.Menu(pystray.MenuItem('Quit', quit_action))
    icon = pystray.Icon("name", image, "Minecraft Monitor", menu)
    
    # Run the monitor in a separate thread
    monitor_thread = threading.Thread(target=monitor_loop, args=(icon,))
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Run the tray icon (this blocks until icon.stop() is called)
    icon.run()

def enforce_single_instance():
    current_pid = os.getpid()
    count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check for python processes
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                # Check if this script is in the command line
                if cmdline and any('minecraft_status_monitor.py' in str(arg) for arg in cmdline):
                    if proc.info['pid'] != current_pid:
                        print(f"Another instance found (PID: {proc.info['pid']}). Exiting.")
                        return False
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return True

if __name__ == "__main__":
    if enforce_single_instance():
        main()
