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
    filename = f"{message.chat.id}_{message.message_id}.mp3"

    try:
        # Поиск трека через Deezer для получения красивого названия и автора
        deezer_url = f"https://api.deezer.com/search?q={query}"
        response = requests.get(deezer_url).json()

        if response.get('data'):
            track_info = response['data'][0]
            title = track_info['title']
            artist = track_info['artist']['name']
            search_query = f"{artist} - {title}"
        else:
            # Если Deezer не нашел, ищем напрямую по запросу пользователя через YouTube
            search_query = query

        # Настройки yt-dlp для скачивания полного аудио
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': filename,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{search_query}"])

        # Отправка файла в Telegram
        if os.path.exists(filename):
            with open(filename, 'rb') as audio:
                bot.send_audio(
                    message.chat.id, 
                    audio, 
                    caption=f"🎵 По запросу: {query}"
                )
            os.remove(filename)
            bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
        else:
            bot.edit_message_text("❌ Не удалось найти или загрузить аудиофайл.", chat_id=message.chat.id, message_id=status_msg.message_id)

    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text("⚠️ Произошла ошибка при скачивании трека.", chat_id=message.chat.id, message_id=status_msg.message_id)
        if os.path.exists(filename):
            os.remove(filename)

bot.infinity_polling()

