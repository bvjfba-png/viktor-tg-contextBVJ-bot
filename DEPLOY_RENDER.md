# Деплой бота на Render.com (бесплатно)

На Render бесплатный тариф есть только для **Web Service**. Бот доработан: при запуске поднимается минимальный HTTP‑сервер на порту `PORT` (его задаёт Render), чтобы платформа считала сервис живым. Сам бот работает как раньше (polling).

---

## 1. Регистрация и репозиторий

1. Зайди на [render.com](https://render.com) и войди через **GitHub**.
2. В правом верхнем углу нажми **New** → **Web Service** (именно Web Service, не Background Worker — он платный).
3. Подключи репозиторий **bvjfba-png/viktor-tg-contextBVJ-bot** (если ещё не подключён — выбери его из списка и нажми **Connect**).

---

## 2. Настройки сервиса

Заполни форму:

| Поле | Значение |
|------|----------|
| **Name** | Любое, например `viktor-context-bot` |
| **Region** | Выбери ближайший (например Frankfurt) |
| **Branch** | `main` |
| **Root Directory** | Оставь пустым |
| **Runtime** | **Python 3** |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python bot.py` |
| **Instance Type** | **Free** |

В репозитории есть файл **`.python-version`** (`3.12.8`) — так бот не собирается на **Python 3.14** по умолчанию (меньше сюрпризов с asyncio). Если Render всё ещё берёт 3.14, в **Environment** добавь **`PYTHON_VERSION`** = `3.12.8`.

---

## 3. Переменные окружения

В блоке **Environment Variables** добавь (кнопка **Add Environment Variable**):

| Key | Value |
|-----|--------|
| `TELEGRAM_TOKEN` | Токен от @BotFather |
| `GITHUB_TOKEN` | GitHub Personal Access Token |
| `GITHUB_REPO` | Репозиторий для контекста, например `bvjfba-png/viktor-context` |
| `ALLOWED_USER_ID` | Твой Telegram ID (число, например `378494233`) |
| `GROQ_API_KEY` | **Голосовые бесплатно:** ключ с [console.groq.com](https://console.groq.com/keys) (регистрация бесплатна, лимиты щедрые, Whisper через API) |
| `OPENAI_API_KEY` | Альтернатива для голосовых — платный Whisper OpenAI, если не хочешь Groq |
| `WHISPER_LANGUAGE` | Опционально: `ru`, по умолчанию русский |

Если заданы оба ключа, сначала используется **Groq**. Без `GROQ_API_KEY` и без `OPENAI_API_KEY` текст и фото работают; голосовые — только после добавления одного из ключей.

Значения бери из своего локального `.env`.

---

## 4. Деплой

Нажми **Create Web Service**. Render соберёт проект и запустит бота. В логах должны появиться строки вроде `Health server on port 10000` и `🤖 Bot started`.

Сервису выдадут URL вида `https://viktor-context-bot.onrender.com` — он нужен для следующего шага.

---

## 5. Чтобы бот не «засыпал» (важно для Free)

На бесплатном тарифе сервис **отключается после 15 минут без входящих HTTP‑запросов**. Пока он спит, бот не получает сообщения.

**Что сделать:** настроить бесплатный мониторинг, который раз в 10–14 минут открывает твой URL:

1. Зайди на [uptimerobot.com](https://uptimerobot.com) (бесплатно).
2. Создай **Monitor**:
   - **Monitor Type**: HTTP(s)
   - **URL**: твой Render URL, например `https://viktor-context-bot.onrender.com`
   - **Monitoring Interval**: 5 или 10 минут
3. Сохрани. UptimeRobot будет пинговать сервис, и Render не будет его останавливать.

После этого бот будет работать постоянно в рамках бесплатного тарифа.

---

## 6. Проверка

- В Render: вкладка **Logs** — есть `Bot started`, нет ошибок про токены.
- В Telegram: отправь боту `/start` или любое сообщение — должен ответить.

Если что-то пойдёт не так, проверь переменные окружения и логи сборки/запуска в Render.
