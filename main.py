import os
import sqlite3
from flask import Flask, request
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes
from utils.pdf_generator import generate_pdf  # генерация PDF из заметок
from utils.logger import log_event  # логгер (будем расширять)

# === Переменные окружения ===
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")
print(f"\U0001F680 TOKEN: {TOKEN}")
print(f"\U0001F310 WEBHOOK_URL: {WEBHOOK_URL}")

# === Flask-приложение и Telegram-приложение ===
app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# === Webhook ===
@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok", 200

# === SQLite: инициализация базы ===
def init_db():
    conn = sqlite3.connect("tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

init_db()

# === Логирование в БД ===
def log_to_db(entry_type, content):
    conn = sqlite3.connect("tracker.db")
    c = conn.cursor()
    c.execute("INSERT INTO logs (type, content) VALUES (?, ?)", (entry_type, content))
    conn.commit()
    conn.close()

# === Команды ===
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
/report — текстовый отчёт
/pdf — PDF с отчётом
""")

async def training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entry = ' '.join(context.args)
    log_to_db("training", entry)
    await update.message.reply_text(f"Тренировка записана: {entry}")

async def reading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entry = ' '.join(context.args)
    log_to_db("reading", entry)
    await update.message.reply_text(f"Чтение записано: {entry}")

async def supplements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entry = ' '.join(context.args)
    log_to_db("supplements", entry)
    await update.message.reply_text(f"Добавки записаны: {entry}")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("tracker.db")
    c = conn.cursor()
    c.execute("SELECT type, content, timestamp FROM logs ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("Нет записей.")
        return
    text = "\n".join([f"[{r[2]}] {r[0].capitalize()}: {r[1]}" for r in rows])
    await update.message.reply_text("📝 Отчёт:\n" + text)

async def pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_path = generate_pdf()
    with open(file_path, "rb") as f:
        await update.message.reply_document(InputFile(f, filename="report.pdf"))

# === Регистрируем хендлеры ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("training", training))
application.add_handler(CommandHandler("reading", reading))
application.add_handler(CommandHandler("supplements", supplements))
application.add_handler(CommandHandler("report", report))
application.add_handler(CommandHandler("pdf", pdf))
