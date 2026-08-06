import os
import requests
import telebot
import yt_dlp

TOKEN = '8352638031:AAGh1SO6D8-Lk1EscLCZX_z0kae6BSnMCCc'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Напиши мне название песни или исполнителя, и я пришлю аудиофайл!")

@bot.message_handler(func=lambda message: True)
def search_and_send_music(message):
    query = message.text
    status_msg = bot.reply_to(message, f"🔎 Ищу и скачиваю «{query}»...")
    
    filename_template = f"{message.chat.id}_{message.message_id}.%(ext)s"

    try:
        # Настройки yt-dlp: ищем через SoundCloud (scsearch), а не YouTube!
        # SoundCloud НЕ блокирует IP-адреса Render.
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': filename_template,
            'quiet': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Префикс scsearch1: ищет 1-й рабочий трек на SoundCloud
            info = ydl.extract_info(f"scsearch1:{query}", download=True)
            
            if 'entries' in info and len(info['entries']) > 0:
                track = info['entries'][0]
                downloaded_file = ydl.prepare_filename(track)
                title = track.get('title', query)
                artist = track.get('uploader', 'Music')
            else:
                downloaded_file = None

        if downloaded_file and os.path.exists(downloaded_file):
            with open(downloaded_file, 'rb') as audio:
                bot.send_audio(
                    message.chat.id, 
                    audio, 
                    caption=f"🎵 {title}",
                    title=title,
                    performer=artist
                )
            os.remove(downloaded_file)
            bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
        else:
            bot.edit_message_text("❌ Трек не найден.", chat_id=message.chat.id, message_id=status_msg.message_id)

    except Exception as e:
        print(f"Error details: {e}")
        bot.edit_message_text("⚠️ Ошибка сервера. Попробуй другой запрос.", chat_id=message.chat.id, message_id=status_msg.message_id)

bot.remove_webhook()
bot.infinity_polling(skip_pending=True)
