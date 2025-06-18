import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes
from utils.logger import log_event
from utils.pdf_generator import generate_pdf

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

application = Application.builder().token(TOKEN).build()

@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run_coroutine_threadsafe(
        application.update_queue.put(update),
        application._loop
    )
    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

# === Команды ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот. Команды: /add /training /reading /supplements /report /pdf")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entry = ' '.join(context.args)
    log_event("task", entry)
    await update.message.reply_text(f"Задача добавлена: {entry}")

async def training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entry = ' '.join(context.args)
    log_event("training", entry)
    await update.message.reply_text(f"Тренировка записана: {entry}")

async def reading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entry = ' '.join(context.args)
    log_event("reading", entry)
    await update.message.reply_text(f"Чтение записано: {entry}")

async def supplements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entry = ' '.join(context.args)
    log_event("supplements", entry)
    await update.message.reply_text(f"Добавки записаны: {entry}")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import json
    try:
        with open("db.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            raise ValueError
    except:
        await update.message.reply_text("Нет записей.")
        return
    text = "\n".join([f"{entry['type'].capitalize()}: {entry['content']}" for entry in data])
    await update.message.reply_text("📝 Отчёт:\n" + text)

async def pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_path = generate_pdf()
    with open(file_path, "rb") as f:
        await update.message.reply_document(InputFile(f, filename="report.pdf"))

# === Регистрируем команды ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add))
application.add_handler(CommandHandler("training", training))
application.add_handler(CommandHandler("reading", reading))
application.add_handler(CommandHandler("supplements", supplements))
application.add_handler(CommandHandler("report", report))
application.add_handler(CommandHandler("pdf", pdf))

# === Установка Webhook ===
async def set_webhook():
    try:
        await application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
        print(f"✅ Webhook установлен: {WEBHOOK_URL}/{TOKEN}")
    except Exception as e:
        print("❌ Ошибка установки webhook:", e)

async def main():
    await application.initialize()
    await set_webhook()
    await application.start()
    await application.updater.start_polling()  # нужно, чтобы обрабатывать update_queue
    await application.updater.wait_for_stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
        app.run(host="0.0.0.0", port=10000)
    except Exception as e:
        print("❌ Ошибка запуска:", e)
