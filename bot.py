import os
import requests
import telebot

TOKEN = '8895343882:AAHAnxW5-AEohWLPexGoUFYqwRhJ-NfGrAs'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🎵 Напиши название песни или исполнителя, и я найду MP3-файл!")

@bot.message_handler(func=lambda message: True)
def search_and_send_music(message):
    query = message.text
    msg = bot.reply_to(message, "🔍 Ищу аудиофайл в интернете...")

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        api_url = f"https://api.deezer.com/search?q={query}"
        response = requests.get(api_url, headers=headers).json()

        if not response.get('data'):
            bot.edit_message_text("❌ Песня не найдена. Попробуй уточнить запрос.", message.chat.id, msg.message_id)
            return

        track = response['data'][0]
        title = track['title']
        artist = track['artist']['name']
        audio_url = track['preview']

        filename = "temp_song.mp3"
        audio_data = requests.get(audio_url, headers=headers).content

        with open(filename, 'wb') as f:
            f.write(audio_data)

        with open(filename, 'rb') as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                title=title,
                performer=artist
            )

        bot.delete_message(message.chat.id, msg.message_id)

        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        bot.edit_message_text("❌ Не удалось загрузить этот трек. Попробуй другое название!", message.chat.id, msg.message_id)

bot.infinity_polling()
