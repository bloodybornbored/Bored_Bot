import os
import json
import tempfile
from flask import Flask, request
from telegram import Update, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from utils.logger import log_event
from utils.pdf_generator import generate_pdf
import speech_recognition as sr
from pydub import AudioSegment

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот-трекер. Команды: /help")

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
🤖 *Команды бота:*

📋 *Заметки и задачи*
/add [текст] — добавить задачу  
/training gym [текст] — тренировка в зале  
/training home [текст] — домашняя тренировка  
/report — краткий отчёт  
/pdf — выгрузка в PDF

📚 *Книги*
/booknote [название] [заметка] — заметка по книге  
/addbook [название] — добавить в библиотеку  
/books — список прочитанных книг  
/bookpdf [название] — PDF по заметкам книги

🎬 *Фильмы и игры*
/filmlog [текст] — заметка по фильму  
/gamelog [текст] — заметка по игре

💊 *Добавки и напоминания*
/supplement [текст] — приём добавки  
/remind [время] [текст] — напоминание (пример: /remind 15:00 массаж)  
/dailylog — активные напоминания

🧠 *Другое*
/mindmap — интеллект-карта (PDF)  
/help — список команд
"""
    await update.message.reply_markdown(text)

# Обработка голосовых сообщений
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.voice.file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".oga") as temp_oga:
        await file.download_to_drive(temp_oga.name)
        temp_wav = temp_oga.name.replace(".oga", ".wav")
        AudioSegment.from_ogg(temp_oga.name).export(temp_wav, format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_wav) as source:
            audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio, language="ru-RU")
                log_event("voice", text)
                await update.message.reply_text(f"🔊 Распознано: {text}")
            except:
                await update.message.reply_text("❌ Не удалось распознать голосовое сообщение.")

# Хендлеры
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.VOICE, handle_voice))

# Webhook маршрут
@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok", 200

# Запуск
if __name__ == "__main__":
    application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    print("🔗 Webhook установлен")
    app.run(port=int(os.environ.get("PORT", 10000)), host="0.0.0.0")
