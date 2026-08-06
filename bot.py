import os
import time
import threading
from flask import Flask
import telebot
import yt_dlp

# 1. Задаем токен
TOKEN = '8352638031:AAGh1SO6D8-Lk1EscLCZX_z0kae6BSnMCCc'
bot = telebot.TeleBot(TOKEN)

# 2. Функция прогресс-бара
def make_progress_bar(percent):
    filled_len = int(10 * percent // 100)
    bar = '█' * filled_len + '░' * (10 - filled_len)
    return f"[{bar}] {percent:.1f}%"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Напиши мне название песни или исполнителя, и я пришлю аудиофайл!")

@bot.message_handler(func=lambda message: True)
def search_and_send_music(message):
    query = message.text
    status_msg = bot.reply_to(message, f"🔎 Ищу «{query}»...")
    
    filename_template = f"{message.chat.id}_{message.message_id}.%(ext)s"
    last_update_time = [0]

    def progress_hook(d):
        if d['status'] == 'downloading':
            current_time = time.time()
            if current_time - last_update_time[0] > 2:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                
                if total > 0:
                    percent = (downloaded / total) * 100
                    bar = make_progress_bar(percent)
                    try:
                        bot.edit_message_text(
                            f"⬇️ **Скачивание трека...**\n{bar}", 
                            chat_id=message.chat.id, 
                            message_id=status_msg.message_id,
                            parse_mode='Markdown'
                        )
                        last_update_time[0] = current_time
                    except Exception:
                        pass

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': filename_template,
            'quiet': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'progress_hooks': [progress_hook]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch1:{query}", download=True)
            
            if 'entries' in info and len(info['entries']) > 0:
                track = info['entries'][0]
                downloaded_file = ydl.prepare_filename(track)
                title = track.get('title', query)
                artist = track.get('uploader', 'Music')
            else:
                downloaded_file = None

        if downloaded_file and os.path.exists(downloaded_file):
            bot.edit_message_text("⬆️ **Отправка аудиотрека в чат...**", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown')
            
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

# 3. Запуск самого бота в ДОЧЕРНЕМ потоке
def run_bot():
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run_bot, daemon=True).start()

# 4. Запуск Flask в ГЛАВНОМ потоке на порту Render (чтобы деплой мгновенно прошел)
app = Flask('')

@app.route('/')
def main():
    return "OK"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
