# 🧠 NexusBot — AI-консультант с долгосрочной памятью

Telegram-бот с подключённой LLM, персистентной историей диалогов и переключаемыми ролями.  
Работает через [ProxyAPI](https://proxyapi.ru) — без VPN, оплата в рублях.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?style=flat&logo=telegram)](https://aiogram.dev)
[![SQLite](https://img.shields.io/badge/SQLite-persistent_memory-003B57?style=flat&logo=sqlite)](https://sqlite.org)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![ProxyAPI](https://img.shields.io/badge/ProxyAPI-OpenAI--compatible-412991?style=flat)](https://proxyapi.ru)

---

## 📽 Демо

[NexusBot demo](assets/demo.gif)

**Что показать на записи (сценарий ~30 сек):**
1. `/start` — бот приветствует, показывает роль
2. Обычный вопрос → ответ со строкой стоимости внизу
3. `/mode` → выбор роли «Разработчик» → вопрос про код → ответ
4. `/reset` → подтверждение очистки
5. Тот же вопрос снова → бот не помнит контекст (демонстрация сброса)

---

## ✨ Возможности

| | Функция | Детали |
|---|---|---|
| 🧠 | **Персистентная память** | История в SQLite — сохраняется между перезапусками |
| 🎭 | **5 настраиваемых ролей** | Помощник, Разработчик, Аналитик, Редактор, Учитель |
| 🔄 | **Смена роли** | `/mode` с inline-кнопками, роли меняются в `prompts.json` без правок кода |
| 🗑 | **Сброс контекста** | `/reset` очищает историю, роль сохраняется |
| 🎬 | **Генерация видео** | `/video <промпт>` через Sora 2 (ProxyAPI) |
| 💰 | **Стоимость запроса** | Токены + цена в ₽ после каждого ответа (курс ЦБ РФ live) |
| 🐳 | **Docker-ready** | Один `docker-compose up` — бот запущен |
| 🔌 | **Работа в РФ** | SOCKS5 через Karing (порт 3067), настраивается в `.env` |

---

## 🗂 Структура проекта

```
nexusbot/
├── main.py               # Точка входа, все обработчики команд
├── config.py             # Переменные окружения
├── db.py                 # SQLite: история и роли пользователей
├── prompts.json          # Роли и системные промпты
├── utils/
│   ├── llm.py            # Клиент LLM (ProxyAPI + SOCKS5)
│   ├── video.py          # Генерация видео Sora 2 (polling)
│   └── cost.py           # Стоимость токенов + курс ЦБ РФ
├── data/
│   └── dialogs.db        # SQLite-база (создаётся автоматически)
├── assets/
│   └── demo.gif          # Демо-запись для README
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

---

## 🚀 Быстрый старт

### Вариант А — Docker (рекомендуется)

```bash
# 1. Клонировать
git clone https://github.com/KirillTomenko/-AI-Video-Generator.git
cd -AI-Video-Generator

# 2. Настроить .env
cp .env.example .env
# → вставить BOT_TOKEN и PROXY_API_KEY

# 3. Запустить
docker-compose up -d --build

# Логи
docker-compose logs -f
```

### Вариант Б — локально (Windows)

```powershell
py -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # заполнить токены
python main.py
```

---

## ⚙️ Переменные окружения

| Переменная | Обязательная | Описание |
|---|---|---|
| `BOT_TOKEN` | ✅ | Токен от @BotFather |
| `PROXY_API_KEY` | ✅ | Ключ от [proxyapi.ru](https://proxyapi.ru) |
| `LLM_MODEL` | — | Модель LLM (по умолч. `gpt-4o-mini`) |
| `MAX_HISTORY_MESSAGES` | — | Глубина контекста (по умолч. `10`) |
| `SOCKS5_PROXY` | — | Прокси Karing (по умолч. `socks5://host.docker.internal:3067`) |
| `VIDEO_MODEL` | — | Модель видео (по умолч. `sora-2`) |
| `VIDEO_DURATION` | — | Длина видео в сек (по умолч. `4`) |

---

## 📋 Команды бота

| Команда | Действие |
|---|---|
| `/start` | Приветствие, текущая роль |
| `/mode` | Выбрать роль через inline-кнопки |
| `/reset` | Очистить историю диалога |
| `/video <промпт>` | Сгенерировать видео (Sora 2) |

---

## 🧠 Архитектура памяти

```
Пользователь пишет сообщение
         ↓
db.add_message()  →  SQLite dialogs.db
         ↓
db.get_history()  →  последние N сообщений
         ↓
[system_prompt] + [history]  →  LLM (ProxyAPI)
         ↓
ответ  →  db.add_message()  +  пользователю
```

История хранится в SQLite — при перезапуске бота или пересборке Docker-образа каждый пользователь продолжает диалог с того места, где остановился. База монтируется через volume (`./data:/app/data`).

---

## 🎭 Роли (prompts.json)

Роли редактируются в `prompts.json` без изменений кода — достаточно перезапустить бота.

| Ключ | Название | Описание |
|---|---|---|
| `assistant` | Обычный помощник | Повседневные задачи |
| `developer` | Помощник разработчика | Код, архитектура, ревью |
| `analyst` | Аналитик | Данные, решения, риски |
| `writer` | Редактор текстов | Посты, статьи, копирайтинг |
| `teacher` | Учитель | Объясняет сложное просто |

---

## 💰 Стоимость

| | Цена |
|---|---|
| gpt-4o-mini (вход) | $0.15 / 1M токенов |
| gpt-4o-mini (выход) | $0.60 / 1M токенов |
| Sora 2 (видео) | ~27 ₽/сек → 4 сек ≈ 108 ₽ |

Курс USD/RUB берётся с API ЦБ РФ при каждом запросе.

---

## 🔧 Стек

`Python 3.11` · `aiogram 3.x` · `SQLite` · `httpx` · `Docker` · `ProxyAPI` · `Sora 2`
