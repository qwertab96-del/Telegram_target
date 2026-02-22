#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import time
import json
import uuid
from concurrent.futures import ThreadPoolExecutor

# Python 3.13 uchun audioop fix
if sys.version_info >= (3, 13):
    try:
        import audioop_lts as audioop
    except ImportError:
        pass

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

from shazamio import Shazam
import yt_dlp

# SOZLAMALAR
BOT_TOKEN = "8572748050:AAHD6JCqzaTpDcBu6qDc4dWJiLHRhgXOxow"
BOT_USERNAME = "@Saveds_bot"

BASE_DIR = Path("/sdcard/Download/SavedsBot")
TEMP_DIR = Path("/tmp/saveds_bot")
BASE_DIR.mkdir(exist_ok=True, parents=True)
TEMP_DIR.mkdir(exist_ok=True, parents=True)

COOKIES_FILE = Path("/root/bot/cookies.txt")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 500 PARALLEL
thread_pool = ThreadPoolExecutor(max_workers=500)
active_downloads = 0
total_downloads = 0
active_users_count = 0
stats_lock = asyncio.Lock()
user_counter_lock = asyncio.Lock()

# TILLAR
TRANSLATIONS = {
    'uz': {
        'start': "🌟 Assalomu alaykum!\n\n📥 Instagram, TikTok, YouTube linklarini yuboring",
        'main_menu': "🏠 Asosiy menyu",
        'download': "📥 Yuklab olish",
        'profile': "📊 Profil",
        'help': "🆘 Yordam",
        'add_group': "👥 Guruhga qo'shish",
        'back': "🔙 Orqaga",
        'send_link': "📥 Link yuboring:",
        'downloading': "⚡️ Yuklanmoqda...",
        'downloading_video': "📥 Video yuklanmoqda...",
        'sending_video': "📤 Video yuborilmoqda...",
        'identifying_song': "🎵 Qo'shiq aniqlanmoqda...",
        'searching_music': "🔍 Musiqa qidirilmoqda...",
        'downloading_music': "📥 Musiqa yuklanmoqda...",
        'completed': "✅ Bajarildi! {time} sek",
        'error': "❌ Xatolik yuz berdi!",
        'invalid_link': "❌ Noto'g'ri link! Faqat Instagram, TikTok, YouTube",
        'profile_text': "📊 PROFIL\n\n👤 {name}\n📥 Yuklamalar: {downloads}",
        'help_text': "🆘 YORDAM\n\n📥 Platformalar: Instagram, TikTok, YouTube\n📞 Admin: @Yaxyo_02",
        'group_text': "👥 Guruhga qo'shish uchun meni guruhga qo'shing va admin qiling!",
        'song_found': "🎵 {title} - {artist}",
        'video_caption': "✨ @{username} orqali yuklab olindi",
        'music_caption': "🎵 {title} - {artist}\n\n✨ @{username}",
        'active': "⚡️ Aktiv: {count}",
        'users': "👥 Foydalanuvchilar: {count}",
        'music_not_found': "❌ Musiqa topilmadi, videodan audio ajratildi",
        'sending_audio': "🎵 Audio yuborilmoqda...",
        'parallel': "⚡️ 500 PARALLEL - NAVBAT YO'Q"
    },
    'ru': {
        'start': "🌟 Здравствуйте!\n\n📥 Отправляйте ссылки Instagram, TikTok, YouTube",
        'main_menu': "🏠 Главное меню",
        'download': "📥 Скачать",
        'profile': "📊 Профиль",
        'help': "🆘 Помощь",
        'add_group': "👥 Добавить в группу",
        'back': "🔙 Назад",
        'send_link': "📥 Отправьте ссылку:",
        'downloading': "⚡️ Загрузка...",
        'downloading_video': "📥 Видео загружается...",
        'sending_video': "📤 Видео отправляется...",
        'identifying_song': "🎵 Песня определяется...",
        'searching_music': "🔍 Поиск музыки...",
        'downloading_music': "📥 Музыка загружается...",
        'completed': "✅ Готово! {time} сек",
        'error': "❌ Ошибка!",
        'invalid_link': "❌ Неверная ссылка! Только Instagram, TikTok, YouTube",
        'profile_text': "📊 ПРОФИЛЬ\n\n👤 {name}\n📥 Загрузок: {downloads}",
        'help_text': "🆘 ПОМОЩЬ\n\n📥 Платформы: Instagram, TikTok, YouTube\n📞 Admin: @Yaxyo_02",
        'group_text': "👥 Добавьте меня в группу и сделайте админом!",
        'song_found': "🎵 {title} - {artist}",
        'video_caption': "✨ @{username}",
        'music_caption': "🎵 {title} - {artist}\n\n✨ @{username}",
        'active': "⚡️ Активно: {count}",
        'users': "👥 Пользователей: {count}",
        'music_not_found': "❌ Музыка не найдена, аудио из видео",
        'sending_audio': "🎵 Аудио отправляется...",
        'parallel': "⚡️ 500 ПАРАЛЛЕЛЬНО - ОЧЕРЕДИ НЕТ"
    },
    'en': {
        'start': "🌟 Hello!\n\n📥 Send Instagram, TikTok, YouTube links",
        'main_menu': "🏠 Main menu",
        'download': "📥 Download",
        'profile': "📊 Profile",
        'help': "🆘 Help",
        'add_group': "👥 Add to group",
        'back': "🔙 Back",
        'send_link': "📥 Send link:",
        'downloading': "⚡️ Downloading...",
        'downloading_video': "📥 Video downloading...",
        'sending_video': "📤 Video sending...",
        'identifying_song': "🎵 Identifying song...",
        'searching_music': "🔍 Searching music...",
        'downloading_music': "📥 Downloading music...",
        'completed': "✅ Completed! {time} sec",
        'error': "❌ Error!",
        'invalid_link': "❌ Invalid link! Only Instagram, TikTok, YouTube",
        'profile_text': "📊 PROFILE\n\n👤 {name}\n📥 Downloads: {downloads}",
        'help_text': "🆘 HELP\n\n📥 Platforms: Instagram, TikTok, YouTube\n📞 Admin: @Yaxyo_02",
        'group_text': "👥 Add me to group and make admin!",
        'song_found': "🎵 {title} - {artist}",
        'video_caption': "✨ @{username}",
        'music_caption': "🎵 {title} - {artist}\n\n✨ @{username}",
        'active': "⚡️ Active: {count}",
        'users': "👥 Users: {count}",
        'music_not_found': "❌ Music not found, audio from video",
        'sending_audio': "🎵 Sending audio...",
        'parallel': "⚡️ 500 PARALLEL - NO QUEUE"
    }
}

stats_file = BASE_DIR / "stats.json"

def load_stats():
    if stats_file.exists():
        with open(stats_file, 'r') as f:
            return json.load(f)
    return {'users': {}}

def save_stats(stats):
    with open(stats_file, 'w') as f:
        json.dump(stats, f)

def get_user_lang(user_id):
    stats = load_stats()
    return stats['users'].get(str(user_id), {}).get('lang', 'uz')

def set_user_lang(user_id, lang):
    stats = load_stats()
    if str(user_id) not in stats['users']:
        stats['users'][str(user_id)] = {}
    stats['users'][str(user_id)]['lang'] = lang
    save_stats(stats)

def get_text(user_id, key, **kwargs):
    lang = get_user_lang(user_id)
    if lang not in TRANSLATIONS:
        lang = 'uz'
    text = TRANSLATIONS[lang].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text

def add_download(user_id):
    stats = load_stats()
    if str(user_id) not in stats['users']:
        stats['users'][str(user_id)] = {'downloads': 0}
    stats['users'][str(user_id)]['downloads'] = stats['users'][str(user_id)].get('downloads', 0) + 1
    save_stats(stats)
    global total_downloads
    total_downloads += 1

def get_downloads(user_id):
    stats = load_stats()
    return stats['users'].get(str(user_id), {}).get('downloads', 0)

def detect_platform(url):
    url = url.lower()
    if 'youtube.com' in url or 'youtu.be' in url:
        return 'YouTube'
    if 'instagram.com' in url:
        return 'Instagram'
    if 'tiktok.com' in url:
        return 'TikTok'
    return None

# VIDEO YUKLASH
def download_video_worker(url, out_dir):
    try:
        output_dir = Path(out_dir)
        opts = {
            'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
            'quiet': True,
            'format': 'best[filesize<50M]/best',
            'socket_timeout': 30,
        }
        if COOKIES_FILE.exists():
            opts['cookiefile'] = str(COOKIES_FILE)
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fname = ydl.prepare_filename(info)
            path = Path(fname)
            if not path.exists():
                path = Path(str(fname).replace('.webm', '.mp4'))
            return {'ok': True, 'path': str(path), 'title': info.get('title', 'Video')}
    except Exception as e:
        logger.error(f"Video xatosi: {e}")
        return {'ok': False, 'error': str(e)}

async def download_video_async(url, out_dir):
    global active_downloads
    async with stats_lock:
        active_downloads += 1
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(thread_pool, download_video_worker, url, out_dir)
        return result
    finally:
        async with stats_lock:
            active_downloads -= 1

# SHAZAM
async def shazam_song(audio_path):
    try:
        shazam = Shazam()
        with open(audio_path, 'rb') as f:
            result = await shazam.recognize(f.read())
        if result and 'track' in result:
            track = result['track']
            return {'ok': True, 'title': track.get('title', ''), 'artist': track.get('subtitle', '')}
        return {'ok': False}
    except Exception as e:
        logger.error(f"Shazam xatosi: {e}")
        return {'ok': False}

# MUSIQA YUKLASH
def download_music_worker(title, artist):
    try:
        query = f"{title} {artist} official audio"
        opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(TEMP_DIR / f"{title} - {artist}.%(ext)s"),
            'quiet': True,
            'default_search': 'ytsearch1',
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            if info and 'entries' in info and info['entries']:
                fname = ydl.prepare_filename(info['entries'][0])
                mp3 = fname.replace('.webm', '.mp3').replace('.m4a', '.mp3')
                path = Path(mp3)
                if path.exists():
                    return path
        return None
    except Exception as e:
        logger.error(f"Musiqa xatosi: {e}")
        return None

async def download_music_async(title, artist):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, download_music_worker, title, artist)

# AUDIO AJRATISH
def extract_audio_worker(video_path):
    try:
        vpath = Path(video_path)
        audio_path = TEMP_DIR / f"{vpath.stem}.mp3"
        cmd = ['ffmpeg', '-i', str(vpath), '-vn', '-acodec', 'libmp3lame', '-y', str(audio_path)]
        subprocess.run(cmd, capture_output=True, timeout=60)
        return str(audio_path) if audio_path.exists() else None
    except Exception as e:
        logger.error(f"Audio xatosi: {e}")
        return None

async def extract_audio_async(video_path):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, extract_audio_worker, video_path)

# TUGMALAR
def lang_menu():
    kb = [
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    return InlineKeyboardMarkup(kb)

def main_menu(uid):
    kb = [
        [InlineKeyboardButton(get_text(uid, 'download'), callback_data="download")],
        [InlineKeyboardButton(get_text(uid, 'profile'), callback_data="profile"), 
         InlineKeyboardButton(get_text(uid, 'help'), callback_data="help")],
        [InlineKeyboardButton(get_text(uid, 'add_group'), callback_data="add_group")]
    ]
    return InlineKeyboardMarkup(kb)

def back_btn(uid):
    return InlineKeyboardMarkup([[InlineKeyboardButton(get_text(uid, 'back'), callback_data="back")]])

# HANDLERLAR
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌟 Assalomu alaykum!\n\n🌐 Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=lang_menu()
    )

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    lang = query.data.replace('lang_', '')
    set_user_lang(uid, lang)
    await query.edit_message_text(
        get_text(uid, 'main_menu'),
        reply_markup=main_menu(uid)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    if data == "back":
        await query.edit_message_text(get_text(uid, 'main_menu'), reply_markup=main_menu(uid))
    elif data == "download":
        await query.edit_message_text(get_text(uid, 'send_link'), reply_markup=back_btn(uid))
    elif data == "profile":
        downloads = get_downloads(uid)
        text = get_text(uid, 'profile_text', name=query.from_user.first_name, downloads=downloads)
        await query.edit_message_text(text, reply_markup=back_btn(uid))
    elif data == "help":
        text = get_text(uid, 'help_text')
        await query.edit_message_text(text, reply_markup=back_btn(uid))
    elif data == "add_group":
        text = get_text(uid, 'group_text')
        await query.edit_message_text(text, reply_markup=back_btn(uid))

# ASOSIY LINK HANDLER
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    url = update.message.text.strip()
    
    global active_users_count

    if not url.startswith('http'):
        return

    platform = detect_platform(url)
    if not platform:
        await update.message.reply_text(get_text(uid, 'invalid_link'), reply_markup=back_btn(uid))
        return

    async with user_counter_lock:
        active_users_count += 1
        current_users = active_users_count

    msg = await update.message.reply_text(
        f"{get_text(uid, 'parallel')}\n"
        f"{get_text(uid, 'users', count=current_users)}\n"
        f"{get_text(uid, 'active', count=active_downloads)}"
    )
    
    start_time = time.time()

    try:
        user_dir = BASE_DIR / str(uid) / datetime.now().strftime("%Y%m%d_%H%M%S")
        user_dir.mkdir(exist_ok=True, parents=True)

        await msg.edit_text(get_text(uid, 'downloading_video'))
        video = await download_video_async(url, str(TEMP_DIR))

        if not video['ok']:
            await msg.edit_text(get_text(uid, 'error'), reply_markup=back_btn(uid))
            return

        vpath = Path(video['path'])
        shutil.copy2(vpath, user_dir / vpath.name)
        add_download(uid)

        await msg.edit_text(get_text(uid, 'sending_video'))
        with open(vpath, 'rb') as f:
            await update.message.reply_video(
                video=f,
                caption=get_text(uid, 'video_caption', username=BOT_USERNAME[1:])
            )

        await msg.edit_text(get_text(uid, 'identifying_song'))
        audio_path = await extract_audio_async(str(vpath))

        if audio_path:
            song = await shazam_song(audio_path)
            
            if song['ok']:
                await msg.edit_text(get_text(uid, 'searching_music'))
                music_path = await download_music_async(song['title'], song['artist'])
                
                if music_path:
                    shutil.copy2(music_path, user_dir / music_path.name)
                    await msg.edit_text(get_text(uid, 'sending_audio'))
                    with open(music_path, 'rb') as f:
                        await update.message.reply_audio(
                            audio=f,
                            title=song['title'],
                            performer=song['artist'],
                            caption=get_text(uid, 'music_caption', 
                                           title=song['title'], 
                                           artist=song['artist'], 
                                           username=BOT_USERNAME[1:])
                        )
                    music_path.unlink()
                else:
                    await msg.edit_text(get_text(uid, 'music_not_found'))
                    with open(audio_path, 'rb') as f:
                        await update.message.reply_audio(
                            audio=f,
                            title=video['title'],
                            performer=platform,
                            caption=get_text(uid, 'music_caption', 
                                           title=video['title'], 
                                           artist=platform, 
                                           username=BOT_USERNAME[1:])
                        )
            else:
                await msg.edit_text(get_text(uid, 'music_not_found'))
                with open(audio_path, 'rb') as f:
                    await update.message.reply_audio(
                        audio=f,
                        title=video['title'],
                        performer=platform,
                        caption=get_text(uid, 'music_caption', 
                                       title=video['title'], 
                                       artist=platform, 
                                       username=BOT_USERNAME[1:])
                    )

            Path(audio_path).unlink()

        elapsed = time.time() - start_time
        await msg.edit_text(
            get_text(uid, 'completed', time=f"{elapsed:.1f}"),
            reply_markup=back_btn(uid)
        )
        
        vpath.unlink()

    except Exception as e:
        logger.error(f"Xato: {e}")
        await msg.edit_text(get_text(uid, 'error'), reply_markup=back_btn(uid))
    
    finally:
        async with user_counter_lock:
            active_users_count -= 1

async def stats_monitor():
    global active_downloads, total_downloads, active_users_count
    while True:
        await asyncio.sleep(10)
        logger.info(
            f"📊 Aktiv: {active_downloads} | "
            f"Jami: {total_downloads} | "
            f"Foydalanuvchilar: {active_users_count}"
        )

def main():
    print("=" * 70)
    print("🚀 SAVEDS GITHUB BOT v37.0")
    print("=" * 70)
    print("📥 Platformalar: Instagram, TikTok, YouTube")
    print(f"⚡️ Parallel threads: {thread_pool._max_workers}")
    print("🌐 Tillar: O'zbek, Русский, English")
    print("🎵 Video + Shazam + Original musiqa")
    print("🚫 NAVBAT YO'Q - 500 PARALLEL")
    print("=" * 70)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(language_selected, pattern='^lang_'))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("✅ Bot ishga tushdi!")
    print("=" * 70)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(stats_monitor())
    app.run_polling()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Bot to'xtatildi!")
    except Exception as e:
        print(f"\n❌ Xatolik: {e}")
        import traceback
        traceback.print_exc()
