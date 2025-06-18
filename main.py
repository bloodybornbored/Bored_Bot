import os
import json
from flask import Flask, request
from telegram import Update, InputFile
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    MessageHandler, filters
)
from utils.logger import log_event
from utils.pdf_generator import generate_pdf
from utils.mindmap_generator import generate_mindmap

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

app = Flask(__name__)

application = Application.builder().token(TOKEN).build()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для трекинга.\n"
        "📌 Команды:\n"
        "/add [текст] — добавить задачу\n"
        "/training [текст] — тренировка (Home или GYM)\n"
        "/reading [текст] — заметка по книге\n"
        "/films [текст] — заметка по фильму\n"
        "/games [текст] — заметка по игре\n"
        "/supplements [текст] — приём добавки\n"
        "/report — отчёт по всем записям\n"
        "/pdf — экспорт PDF\n"
        "/mindmap — mind map\n"
        "/help — список команд"
    )

# Универсальный логер
async def handle_entry(update: Update, context: ContextTypes.DEFAULT_TYPE, entry_type: str):
    text = ' '.join(context.args)
    log_event(entry_type, text)
    await update.message.reply_text(f"✅ Запись добавлена в {entry_type}: {text}")

# Команды
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE): await handle_entry(update, context, "task")
async def training(update: Update, context: ContextTypes.DEFAULT_TYPE): await handle_entry(update, context, "training")
async def reading(update: Update, context: ContextTypes.DEFAULT_TYPE): await handle_entry(update, context, "reading")
async def supplements(update: Update, context: ContextTypes.DEFAULT_TYPE): await handle_entry(update, context, "supplements")
async def films(update: Update, context: ContextTypes.DEFAULT_TYPE): await handle_entry(update, context, "films")
async def games(update: Update, context: ContextTypes.DEFAULT_TYPE): await handle_entry(update, context, "games")

# Команда /report
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("db.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            raise ValueError
    except:
        await update.message.reply_text("Записей нет.")
        return
    text = "\n".join([f"{entry['type'].capitalize()}: {entry['content']}" for entry in data])
    await update.message.reply_text("📝 Отчёт:\n" + text)

# PDF
async def pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_path = generate_pdf()
    with open(file_path, "rb") as f:
        await update.message.reply_document(InputFile(f, filename="report.pdf"))

# Mind Map
async def mindmap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_path = generate_mindmap()
    with open(file_path, "rb") as f:
        await update.message.reply_document(InputFile(f, filename="mindmap.pdf"))

# Help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# Обработка текстовых сообщений
async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команда не распознана. Используй /help для списка команд.")

# Роут вебхука
@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok", 200

# Установка вебхука
@app.before_first_request
def set_webhook():
    application.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    print(f"🔗 Webhook установлен: {WEBHOOK_URL}/{TOKEN}")

# Регистрация хендлеров
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("add", add))
application.add_handler(CommandHandler("training", training))
application.add_handler(CommandHandler("reading", reading))
application.add_handler(CommandHandler("films", films))
application.add_handler(CommandHandler("games", games))
application.add_handler(CommandHandler("supplements", supplements))
application.add_handler(CommandHandler("report", report))
application.add_handler(CommandHandler("pdf", pdf))
application.add_handler(CommandHandler("mindmap", mindmap))
application.add_handler(MessageHandler(filters.TEXT, fallback))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
