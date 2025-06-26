# ---------------------------------------------------
# File Name: ytdl.py (pure code)
# Description: A Pyrogram bot for downloading files from Telegram channels or groups 
#              and uploading them back to Telegram.
# Author: Gagan
# GitHub: https://github.com/devgaganin/
# Telegram: https://t.me/team_spy_pro
# YouTube: https://youtube.com/@dev_gagan
# Created: 2025-01-11
# Last Modified: 2025-01-11
# Version: 2.0.5
# License: MIT License
# ---------------------------------------------------

import os
import re
import asyncio
import logging
import tempfile
import yt_dlp
import requests
import aiohttp
import aiofiles
import random
import string
import time
from mutagen.id3 import ID3, TIT2, TPE1, COMM, APIC
from mutagen.mp3 import MP3
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeVideo
from devgagan import sex as client  # Your existing Telethon client
from devgagan.core.func import screenshot, video_metadata
from devgagantools import fast_upload
from concurrent.futures import ThreadPoolExecutor
from devgagan import app  # Your existing Pyrogram client
from config import config  # Import your existing config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Thread pool for blocking operations
thread_pool = ThreadPoolExecutor(max_workers=4)
ongoing_downloads = {}
user_progress = {}

# Utility functions
def get_random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def download_thumbnail(url, save_path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(save_path, 'wb') as f:
                    await f.write(await response.read())

def get_platform(url):
    if "instagram.com" in url:
        return "instagram", config.INST_COOKIES
    elif "youtube.com" in url or "youtu.be" in url:
        return "youtube", config.YTUB_COOKIES
    return "other", None

# Audio processing
async def process_audio(event, url, cookies):
    try:
        # Create temp files
        temp_cookie_path = None
        random_filename = f"audio_{get_random_string()}"
        download_path = f"{random_filename}.mp3"
        
        # Handle cookies
        if cookies:
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as f:
                f.write(cookies)
                temp_cookie_path = f.name
        
        # Configure yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"{random_filename}.%(ext)s",
            'cookiefile': temp_cookie_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
            'quiet': True,
            'max_filesize': 100 * 1024 * 1024,  # 100MB limit
        }
        
        # Start processing
        progress_msg = await event.reply("⏳ **Starting audio extraction...**")
        
        # Extract audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Extracted Audio')
            thumbnail_url = info.get('thumbnail')
        
        # Edit metadata
        if os.path.exists(download_path):
            audio = MP3(download_path, ID3=ID3)
            try:
                audio.add_tags()
            except Exception:
                pass
            
            audio.tags.add(TIT2(encoding=3, text=title[:30]))
            audio.tags.add(TPE1(encoding=3, text="Team JB"))
            audio.tags.add(COMM(encoding=3, text="Processed by Team SPY"))
            
            if thumbnail_url:
                thumb_path = f"{random_filename}.jpg"
                await download_thumbnail(thumbnail_url, thumb_path)
                with open(thumb_path, 'rb') as img:
                    audio.tags.add(APIC(
                        encoding=3, mime='image/jpeg', type=3, 
                        desc='Cover', data=img.read()
                    ))
                os.remove(thumb_path)
            
            audio.save()
        
        # Upload audio
        await progress_msg.edit("📤 **Uploading audio...**")
        await client.send_file(
            event.chat_id,
            download_path,
            caption=f"🎵 **{title}**\n\n__Powered by Team JB__",
            attributes=[DocumentAttributeVideo(
                duration=0,
                w=0,
                h=0,
                supports_streaming=True
            )]
        )
        
        # Cleanup
        os.remove(download_path)
        await progress_msg.delete()
        
    except yt_dlp.utils.DownloadError as e:
        if "File is larger than max-filesize" in str(e):
            await event.reply("❌ **Audio file exceeds size limit (100MB)**")
        else:
            await event.reply(f"⚠️ **Download error:** {str(e)}")
    except Exception as e:
        logger.exception("Audio processing failed")
        await event.reply(f"🚨 **Error:** {str(e)}")
    finally:
        if temp_cookie_path and os.path.exists(temp_cookie_path):
            os.remove(temp_cookie_path)

# Video processing
async def process_video(event, url, cookies):
    try:
        # Create temp files
        temp_cookie_path = None
        random_filename = f"video_{get_random_string()}"
        download_path = f"{random_filename}.mp4"
        thumb_path = f"{random_filename}.jpg"
        
        # Handle cookies
        if cookies:
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as f:
                f.write(cookies)
                temp_cookie_path = f.name
        
        # Configure yt-dlp
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': download_path,
            'cookiefile': temp_cookie_path,
            'writethumbnail': True,
            'quiet': True,
            'max_filesize': 2 * 1024 * 1024 * 1024,  # 2GB limit
            'max_duration': 3 * 3600,  # 3 hour limit
        }
        
        # Start processing
        progress_msg = await event.reply("⏳ **Starting video download...**")
        
        # Get video info
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Downloaded Video')
            duration = info.get('duration', 0)
            thumbnail_url = info.get('thumbnail')
            
            # Check duration
            if duration > 3 * 3600:
                await progress_msg.edit("❌ **Video exceeds maximum duration (3 hours)**")
                return
            
            # Download
            ydl.download([url])
        
        # Get thumbnail
        if thumbnail_url:
            await download_thumbnail(thumbnail_url, thumb_path)
        
        # Upload video
        await progress_msg.edit("📤 **Uploading video...**")
        await client.send_file(
            event.chat_id,
            download_path,
            caption=f"🎬 **{title}**\n\n__Powered by Team JB__",
            thumb=thumb_path if os.path.exists(thumb_path) else None,
            attributes=[DocumentAttributeVideo(
                duration=duration,
                w=info.get('width', 1280),
                h=info.get('height', 720),
                supports_streaming=True
            )]
        )
        
        # Cleanup
        for path in [download_path, thumb_path]:
            if os.path.exists(path):
                os.remove(path)
        await progress_msg.delete()
        
    except yt_dlp.utils.DownloadError as e:
        if "File is larger than max-filesize" in str(e):
            await event.reply("❌ **Video file exceeds size limit (2GB)**")
        elif "This video is too long" in str(e):
            await event.reply("❌ **Video exceeds maximum duration (3 hours)**")
        else:
            await event.reply(f"⚠️ **Download error:** {str(e)}")
    except Exception as e:
        logger.exception("Video processing failed")
        await event.reply(f"🚨 **Error:** {str(e)}")
    finally:
        if temp_cookie_path and os.path.exists(temp_cookie_path):
            os.remove(temp_cookie_path)

# Command handlers
@client.on(events.NewMessage(pattern="/adl"))
async def audio_download_handler(event):
    user_id = event.sender_id
    if user_id in ongoing_downloads:
        return await event.reply("⏳ You already have an ongoing download. Please wait!")
    
    try:
        if len(event.text.split()) < 2:
            return await event.reply("❌ **Usage:** `/adl <video-url>`")
        
        url = event.text.split()[1]
        platform, cookies = get_platform(url)
        
        ongoing_downloads[user_id] = True
        await process_audio(event, url, cookies)
        
    except Exception as e:
        logger.error(f"Audio download failed: {str(e)}")
        await event.reply(f"⚠️ **Error:** {str(e)}")
    finally:
        ongoing_downloads.pop(user_id, None)

@client.on(events.NewMessage(pattern="/dl"))
async def video_download_handler(event):
    user_id = event.sender_id
    if user_id in ongoing_downloads:
        return await event.reply("⏳ You already have an ongoing download. Please wait!")
    
    try:
        if len(event.text.split()) < 2:
            return await event.reply("❌ **Usage:** `/dl <video-url>`")
        
        url = event.text.split()[1]
        platform, cookies = get_platform(url)
        
        ongoing_downloads[user_id] = True
        await process_video(event, url, cookies)
        
    except Exception as e:
        logger.error(f"Video download failed: {str(e)}")
        await event.reply(f"⚠️ **Error:** {str(e)}")
    finally:
        ongoing_downloads.pop(user_id, None)
