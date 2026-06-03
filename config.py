"""
config.py — загрузка переменных окружения из .env.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram ──────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# ─── ProxyAPI (OpenAI-совместимый, работает в РФ без VPN) ──────────────────────
PROXY_API_KEY: str = os.getenv("PROXY_API_KEY", "")
PROXY_API_BASE: str = os.getenv("PROXY_API_BASE", "https://api.proxyapi.ru/openai/v1")

# ─── LLM модель ────────────────────────────────────────────────────────────────
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

# ─── Параметры памяти ──────────────────────────────────────────────────────────
# Максимальное количество сообщений (пар user/assistant) в контексте
MAX_HISTORY_MESSAGES: int = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))

# ─── Генерация видео через ProxyAPI ───────────────────────────────────────────
VIDEO_MODEL: str = os.getenv("VIDEO_MODEL", "sora-2")
VIDEO_DURATION: int = int(os.getenv("VIDEO_DURATION", "4"))

# ─── Стоимость токенов (gpt-4o-mini, USD за 1M токенов) ──────────────────────
# Актуальные цены: https://proxyapi.ru/
COST_INPUT_PER_1M: float = float(os.getenv("COST_INPUT_PER_1M", "0.15"))   # $0.15
COST_OUTPUT_PER_1M: float = float(os.getenv("COST_OUTPUT_PER_1M", "0.60")) # $0.60

# ─── Валидация ─────────────────────────────────────────────────────────────────
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env")
if not PROXY_API_KEY:
    raise ValueError("PROXY_API_KEY не задан в .env")

# ─── Karing SOCKS5 прокси (для работы в РФ) ───────────────────────────────────
# Karing слушает на localhost:3067 по умолчанию.
# Если прокси не нужен (на сервере вне РФ) — поставь пустую строку в .env
SOCKS5_PROXY: str = os.getenv("SOCKS5_PROXY", "socks5://host.docker.internal:3067")
