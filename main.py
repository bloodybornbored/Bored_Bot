import os
import sqlite3
from flask import Flask, request
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes
from utils.pdf_generator import generate_pdf
from utils.logger import log_event
import datetime
import graphviz

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")
print(f"\U0001F680 TOKEN: {TOKEN}")
print(f"\U0001F310 WEBHOOK_URL: {WEBHOOK_URL}")

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

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

async def books(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = ' '.join(context.args)
    if '-' not in raw:
        await update.message.reply_text("Формат: /books Название - Заметка")
        return
    title, note = map(str.strip, raw.split('-', 1))
    conn = sqlite3.connect("tracker.db")
    c = conn.cursor()
    c.execute("INSERT INTO books (title, notes) VALUES (?, ?)", (title, note))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"Добавлена заметка о книге: {title}")

async def library(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("tracker.db")
    c = conn.cursor()
    c.execute("SELECT title, notes, timestamp FROM books ORDER BY timestamp DESC")
    books = c.fetchall()
    conn.close()
    if not books:
        await update.message.reply_text("Библиотека пуста.")
        return
    text = "\n\n".join([f"{title}\n{notes}\n[{ts}]" for title, notes, ts in books])
    await update.message.reply_text("📚 Библиотека:\n" + text)

async def deletebook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = ' '.join(context.args).strip()
    if not title:
        await update.message.reply_text("Формат: /deletebook Название")
        return
    conn = sqlite3.connect("tracker.db")
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE title = ?", (title,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    if deleted:
        await update.message.reply_text(f"Удалена книга: {title}")
    else:
        await update.message.reply_text(f"Книга не найдена: {title}")

async def bookmap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("tracker.db")
    c = conn.cursor()
    c.execute("SELECT title, notes FROM books")
    books = c.fetchall()
    conn.close()
    if not books:
        await update.message.reply_text("Нет книг для отображения в карте.")
        return
    dot = graphviz.Digraph(format='pdf')
    dot.attr(rankdir='LR')
    dot.node("Библиотека", shape="box")
    for i, (title, notes) in enumerate(books):
        node_id = f"book_{i}"
        dot.node(node_id, f"{title}", shape="ellipse")
        dot.edge("Библиотека", node_id)
        if notes:
            dot.node(f"note_{i}", notes[:80] + ("..." if len(notes) > 80 else ""), shape="note")
            dot.edge(node_id, f"note_{i}")
    file_path = "/tmp/bookmap.pdf"
    dot.render(filename="/tmp/bookmap", cleanup=True)
    with open(file_path, "rb") as f:
        await update.message.reply_document(InputFile(f, filename="bookmap.pdf"))

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        time_str = context.args[0]
        msg = ' '.join(context.args[1:])
        remind_at = datetime.datetime.strptime(time_str, "%H:%M").time()
        now = datetime.datetime.now().time()
        delay = (datetime.datetime.combine(datetime.date.today(), remind_at) - datetime.datetime.combine(datetime.date.today(), now)).total_seconds()
        if delay < 0:
            await update.message.reply_text("Указанное время уже прошло. Попробуй снова.")
            return
        await update.message.reply_text(f"Напомню через {int(delay // 60)} мин: {msg}")
        await context.application.job_queue.run_once(lambda c: c.bot.send_message(chat_id=update.effective_chat.id, text=f"⏰ Напоминание: {msg}"), delay)
    except Exception as e:
        await update.message.reply_text("Формат: /remind HH:MM сообщение")

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
