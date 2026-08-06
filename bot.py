import os
import requests
import telebot
import yt_dlp

TOKEN = '8352638031:AAGh1SO6D8-Lk1EscLCZX_z0kae6BSnMCCc'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Напиши мне название песни или исполнителя, и я скачаю полный MP3-файл!")

@bot.message_handler(func=lambda message: True)
def search_and_send_music(message):
    query = message.text
    status_msg = bot.reply_to(message, f"🔎 Ищу и скачиваю «{query}»...")
    
    # Шаблон имени файла без конвертации
    filename_template = f"{message.chat.id}_{message.message_id}.%(ext)s"

    try:
        # Поиск трека через Deezer для точного названия
        deezer_url = f"https://api.deezer.com/search?q={query}"
        response = requests.get(deezer_url).json()

        if response.get('data'):
            track_info = response['data'][0]
            title = track_info['title']
            artist = track_info['artist']['name']
            search_query = f"{artist} - {title}"
        else:
            title = query
            artist = "Music"
            search_query = query

        # Настройки yt-dlp БЕЗ использования FFmpeg (качаем прямое аудио)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': filename_template,
            'quiet': True,
            'noplaylist': True,
            'nocheckcertificate': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{search_query}", download=True)
            if 'entries' in info and len(info['entries']) > 0:
                downloaded_file = ydl.prepare_filename(info['entries'][0])
            else:
                downloaded_file = None

        # Отправка скачанного файла
        if downloaded_file and os.path.exists(downloaded_file):
            with open(downloaded_file, 'rb') as audio:
                bot.send_audio(
                    message.chat.id, 
                    audio, 
                    caption=f"🎵 {artist} — {title}",
                    title=title,
                    performer=artist
                )
            os.remove(downloaded_file)  # Удаляем временный файл
            bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
        else:
            bot.edit_message_text("❌ Не удалось загрузить аудиофайл.", chat_id=message.chat.id, message_id=status_msg.message_id)

    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text("⚠️ Произошла ошибка при скачивании трека.", chat_id=message.chat.id, message_id=status_msg.message_id)

bot.remove_webhook()
bot.infinity_polling(skip_pending=True)
