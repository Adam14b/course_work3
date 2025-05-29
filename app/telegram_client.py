import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

api_id = 
api_hash = ''
phone_number = ""
channel_username_list = '@finprofit,@omyinvestments,@ecotopor'.split(',')

async def get_channel_messages(limit=200):
    async with TelegramClient('session', api_id, api_hash) as client:
        await client.start(phone=phone_number)

        cleaned_messages = []
        for channel_username in channel_username_list:
            chat_info = await client.get_entity(channel_username)
            messages = await client.get_messages(entity=chat_info, limit=limit)
            
            for message in messages:
                try:
                    video = message.media.video
                except:
                    video = False
                if message.text and not video:
                    channel_username_link = channel_username.lstrip("@")
                    message_link = f"https://t.me/{channel_username_link}/{message.id}"
                    cleaned_messages.append({
                        "text": message.text,
                        "link": message_link,
                        "date": message.date.isoformat()
                    })
        
        return cleaned_messages

def update_messages():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_channel_messages())
    finally:
        loop.close()
