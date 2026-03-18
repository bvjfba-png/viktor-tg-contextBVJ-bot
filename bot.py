import os
import logging
import base64
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
import requests as req
from github import Github, GithubException

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# Не писать в логи полные URL к Telegram (там виден токен)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# ── конфиг из переменных окружения ────────────────────────────────────────────
TELEGRAM_TOKEN  = os.environ["TELEGRAM_TOKEN"]
GITHUB_TOKEN    = os.environ["GITHUB_TOKEN"]
GITHUB_REPO     = os.environ["GITHUB_REPO"]        # "username/repo-name"
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "0"))

g    = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)

# ── утилиты ───────────────────────────────────────────────────────────────────

def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def month() -> str:
    return datetime.now().strftime("%Y-%m")

def time_now() -> str:
    return datetime.now().strftime("%H:%M")

def append_to_file(path: str, content: str) -> None:
    """Дописывает контент в файл. Создаёт файл если не существует."""
    try:
        file = repo.get_contents(path)
        current = file.decoded_content.decode("utf-8")
        repo.update_file(path, f"update {path}", current + content, file.sha)
    except GithubException:
        repo.create_file(path, f"create {path}", content)

def upload_binary(path: str, data: bytes) -> bool:
    """Загружает бинарный файл (фото) напрямую через GitHub API."""
    encoded = base64.b64encode(data).decode("utf-8")
    resp = req.put(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}",
        json={"message": f"add {path}", "content": encoded},
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
    )
    return resp.status_code in (200, 201)

def is_allowed(update: Update) -> bool:
    if not ALLOWED_USER_ID:
        return True
    return update.effective_user.id == ALLOWED_USER_ID

def detect_category(text: str) -> tuple[str, str]:
    """Определяет куда сохранять текст по ключевым словам."""
    t = text.lower()
    workout_words = ["жал", "тяга", "присед", "подтяг", "трениров", " кг", "повтор", "сет", "жим", "бег", "пробеж"]
    metric_words  = ["вес ", "давлен", "пульс", "сон ", "темпер", "анализ", "сахар", "холестер", "самочувств"]

    if any(w in t for w in workout_words):
        return f"health/workouts/{month()}.md", "💪 тренировка"
    elif any(w in t for w in metric_words):
        return f"health/metrics/{month()}.md", "📊 метрика"
    else:
        return f"journal/{month()}.md", "📝 заметка"

# ── обработчики ───────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Привет! Я твой личный архив.\n\n"
        "Просто пиши мне:\n"
        "• *текст* — сохраняю в дневник, тренировки или метрики\n"
        "• *фото* — сохраняю в папку еды (можно добавить подпись)\n\n"
        "Ключевые слова для тренировок: жал, присед, тяга, подтяг, бег, кг, сет\n"
        "Ключевые слова для метрик: вес, давление, пульс, сон, анализ\n"
        "Всё остальное → дневник 📓",
        parse_mode="Markdown"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return

    text  = update.message.text
    path, category = detect_category(text)
    entry = f"\n## {today()} {time_now()}\n{text}\n"

    try:
        append_to_file(path, entry)
        await update.message.reply_text(
            f"✅ Сохранено как {category}\n`{path}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(e)
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return

    photo     = update.message.photo[-1]             # максимальное разрешение
    file_obj  = await context.bot.get_file(photo.file_id)
    img_bytes = await file_obj.download_as_bytearray()

    ts       = datetime.now().strftime("%H%M%S")
    img_path = f"health/food/{today()}_{ts}.jpg"

    try:
        ok = upload_binary(img_path, bytes(img_bytes))
        if not ok:
            await update.message.reply_text("❌ Не удалось загрузить фото")
            return

        # Если есть подпись — пишем её в лог
        caption = update.message.caption or ""
        if caption:
            log_entry = f"\n## {today()} {time_now()}\n{caption}\n"
            append_to_file(f"health/food/{month()}.md", log_entry)

        await update.message.reply_text(
            f"✅ Фото сохранено 🥗\n`{img_path}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(e)
        await update.message.reply_text(f"❌ Ошибка: {e}")

# ── health-check для Render (Web Service должен слушать PORT) ──────────────────

def main() -> None:
    # Render Web Service: порт должен быть открыт ДО долгих операций, иначе
    # деплой висит на «No open ports detected».
    port_str = os.environ.get("PORT")
    if port_str:
        port = int(port_str)

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, *args):
                pass

        httpd = HTTPServer(("0.0.0.0", port), Handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        logger.info("Health server listening on 0.0.0.0:%s (Render)", port)
    else:
        logger.info("PORT not set — health server skipped (локальный запуск)")

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    logger.info("🤖 Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
