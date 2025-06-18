import os
import sqlite3
from flask import Flask, request
from telegram import Update, InputFile, Message
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from utils.pdf_generator import generate_pdf
from utils.logger import log_event
import datetime
import graphviz
import whisper
import tempfile
import ffmpeg

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")
print(f"\U0001F680 TOKEN: {TOKEN}")
print(f"\U0001F310 WEBHOOK_URL: {WEBHOOK_URL}")

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()
model = whisper.load_model("base")

@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok", 200

def init_db():
    conn = sqlite3.connect("tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        notes TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT,
        remind_at TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

init_db()

def log_to_db(entry_type, content):
    conn = sqlite3.connect("tracker.db")
    c = conn.cursor()
    c.execute("INSERT INTO logs (type, content) VALUES (?, ?)", (entry_type, content))
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот-трекер. Команды: /help")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
Доступные команды:
/start — запустить бота
/help — список команд
/training [текст] — запись тренировки
/reading [текст] — заметка о прочитанном
/supplements [текст] — добавки
/books [название] - [заметка] — заметка по книге
/library — список книг из библиотеки
/bookmap — mind map по библиотеке
/deletebook [название] — удалить книгу по названию
/remind [время в формате HH:MM] [сообщение] — напоминание
/report — текстовый отчёт
/pdf — PDF с отчётом
/dailyvoice — голосовая заметка дня

🎙 Распознаются голосовые сообщения:
- С фразами: "книга", "домашняя тренировка", "зал", "фильм", "добавка", "заметка"
""")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as ogg_file:
        await file.download_to_drive(ogg_file.name)
        mp3_path = ogg_file.name.replace(".ogg", ".mp3")
        ffmpeg.input(ogg_file.name).output(mp3_path).run(overwrite_output=True, quiet=True)

    result = model.transcribe(mp3_path)
    text = result["text"].strip().lower()

    # определение категории
    category = "dailyvoice"
    if "книга" in text:
        category = "reading"
    elif "домашняя тренировка" in text:
        category = "home training"
    elif "зал" in text:
        category = "gym"
    elif "фильм" in text:
        category = "film"
    elif "добавка" in text:
        category = "supplements"

    log_to_db(category, text)
    await update.message.reply_text(f"🎙 Голос распознан как '{category}':\n{text}")

async def dailyvoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Просто отправь голосовое сообщение, я его распознаю и добавлю как заметку 📝")

# Остальные команды (training, reading и т.д.) не меняются — оставляем как есть

# Добавляем обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("training", training))
application.add_handler(CommandHandler("reading", reading))
application.add_handler(CommandHandler("supplements", supplements))
application.add_handler(CommandHandler("books", books))
application.add_handler(CommandHandler("library", library))
application.add_handler(CommandHandler("deletebook", deletebook))
application.add_handler(CommandHandler("bookmap", bookmap))
application.add_handler(CommandHandler("remind", remind))
application.add_handler(CommandHandler("report", report))
application.add_handler(CommandHandler("pdf", pdf))
application.add_handler(CommandHandler("dailyvoice", dailyvoice))
application.add_handler(MessageHandler(filters.VOICE, handle_voice))
