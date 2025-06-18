import os
import json
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from utils.logger import log_event
from utils.pdf_generator import generate_pdf

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

@app.before_first_request
def set_webhook():
    if WEBHOOK_URL:
        application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return 'ok'

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я бот с вебхуком. Используй команды: /add /pdf и другие.")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args)
    log_event("note", text)
    await update.message.reply_text(f"📝 Добавлено в заметки: {text}")

async def pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_path = generate_pdf()
    await update.message.reply_document(document=open(file_path, "rb"))

# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add))
application.add_handler(CommandHandler("pdf", pdf))

# Запуск Flask-сервера
if __name__ == '__main__':
    application.initialize()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
