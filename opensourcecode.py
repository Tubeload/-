import os
import yt_dlp
import telebot
from telebot import apihelper

# Устанавливаем глобальный таймаут для всех запросов
apihelper.REQUEST_TIMEOUT = 360  # Устанавливаем таймаут для всех HTTP-запросов (в секундах)
apihelper.SESSION_TIME_TO_LIVE = 60  # Устанавливаем время жизни сессии (в секундах)

# Создаем бота с использованием вашего API ключа
API_TOKEN = 'YOUR_API_KEY'  # Вставьте ваш API ключ
bot = telebot.TeleBot(API_TOKEN)

# Функция для обработки прогресса скачивания
def progress_hook(d, chat_id, message_id):
    if d['status'] == 'downloading':
        # Вычисляем процент скачивания
        percent = d['downloaded_bytes'] / d['total_bytes'] * 100
        percent = round(percent, 2)

        # Обновляем сообщение о скачивании
        bot.edit_message_text(f"Соединение установлено ✅\n\nСкачивание ⬇️\n\nℹ️ Скачано на {percent}%", chat_id=chat_id, message_id=message_id)

# Функция для скачивания видео с YouTube
def download_youtube_video(url, chat_id, message_id):
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
            'socket_timeout': 120,  # Устанавливаем таймаут для сокетов
            'retries': 5,  # Количество повторных попыток
            'progress_hooks': [lambda d: progress_hook(d, chat_id, message_id)],  # Обработчик прогресса
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            return filename
    except Exception as e:
        return str(e)

# Функция для обработки команды start
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "Привет! Отправь мне ссылку на видео с YouTube и я его скачаю.\n\nВы можете прямо сейчас начать поиск в Youtube, введя в строку <blockquote><code>@vid</></>и сделав пробел", parse_mode='html')

# Функция для обработки текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()

    if 'youtube.com' in url or 'youtu.be' in url:
        # Начинаем отправку начального сообщения с прогрессом
        msg = bot.reply_to(message, "Идет соединение с сервером YouTube, пожалуйста, подождите ⏳")
        chat_id = message.chat.id
        message_id = msg.message_id
        
        # Скачиваем видео
        filename = download_youtube_video(url, chat_id, message_id)
        
        if os.path.exists(filename):
            with open(filename, 'rb') as video:
                bot.edit_message_text(f"Скачивание завершено ✅\n\nОтправка видео 🎬\n\n⚠️ Отправка часто занимает больше времени, чем скачивание.\nПожалуйста, проявите терпение.\n\n💡 Отправка 5 минутного видео обычно занимает приблизительно 45 секунд.\n\n💡 Если спустя столь долгое время бот все же не отправил видео, возможно ваше видео настолько большое, что отправить его через Telegram боту непосильно.", chat_id=chat_id, message_id=message_id)
                
                bot.send_chat_action(chat_id, 'upload_video')
                bot.send_video(chat_id, video, timeout=360)
                bot.delete_message(chat_id=chat_id, message_id=message_id)  # Увеличиваем таймаут отправки видео до 120 секунд (2 минуты)
                bot.send_message(chat_id, "<blockquote>Отправка видео завершена ✅\n\nОжидаю следуещую ссылку ⏳</>", parse_mode='html')
                os.remove(filename)
        else:
            bot.reply_to(message, f"Ошибка при скачивании видео с YouTube: <pre>{filename}</>\n\nДля продолжения скачивания вставьте ссылку еще раз", parse_mode='html')

    else:
        bot.reply_to(message, "Пожалуйста, отправьте корректную ссылку на видео Youtube.")


bot.polling(none_stop=True)
