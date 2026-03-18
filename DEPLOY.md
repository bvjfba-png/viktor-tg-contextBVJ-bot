# Деплой бота на Railway

## 1. Подключить репозиторий

1. Зайди на [railway.app](https://railway.app) и войди (через GitHub).
2. **New Project** → **Deploy from GitHub repo**.
3. Выбери репозиторий `bvjfba-png/viktor-tg-contextBVJ-bot`.
4. Railway создаст один сервис и начнёт сборку.

## 2. Команда запуска

Бот — это **worker** (долгий процесс `python bot.py`), а не веб-сервер.  
По умолчанию Railway может искать процесс `web` в Procfile — у нас там `worker`.

**В настройках сервиса задай Start Command:**

- Открой сервис → **Settings** → **Deploy**.
- В поле **Start Command** укажи:  
  `python bot.py`  
  (или оставь пустым, если Railway уже подхватил команду из Procfile).

## 3. Переменные окружения

В Railway: сервис → **Variables** → добавь переменные (значения бери из своего локального `.env`):

| Переменная        | Описание                          |
|-------------------|-----------------------------------|
| `TELEGRAM_TOKEN`  | Токен от @BotFather               |
| `GITHUB_TOKEN`    | GitHub Personal Access Token      |
| `GITHUB_REPO`     | Репозиторий для контекста, напр. `bvjfba-png/viktor-context` |
| `ALLOWED_USER_ID` | Твой Telegram ID (число)          |

После сохранения переменных Railway перезапустит деплой.

## 4. Домен (не нужен)

Публичный URL для этого бота не нужен: он сам опрашивает Telegram через long polling.  
Генерировать домен в Railway для этого сервиса не обязательно.

## 5. Проверка

- Вкладка **Deployments**: последний деплой в статусе **Success**.
- Вкладка **Logs**: в логах должна быть строка вида `Bot started` и отсутствие падений по `TELEGRAM_TOKEN` / `GITHUB_TOKEN`.

После этого бот на Railway будет работать 24/7 (в рамках лимитов твоего плана).
