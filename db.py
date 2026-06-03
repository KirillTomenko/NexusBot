"""
db.py — персистентная память диалогов в SQLite.
История не теряется при перезапуске бота.

Таблицы:
  users   — пользователи и их текущая роль
  messages — история сообщений (храним последние MAX_HISTORY_MESSAGES)
"""
import sqlite3
import json
import logging
from pathlib import Path
from config import MAX_HISTORY_MESSAGES

logger = logging.getLogger(__name__)

DB_PATH = Path("data/dialogs.db")


def init_db() -> None:
    """Создаёт БД и таблицы при первом запуске."""
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                mode        TEXT    NOT NULL DEFAULT 'assistant',
                updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                role        TEXT    NOT NULL,   -- 'user' | 'assistant'
                content     TEXT    NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_user
                ON messages(user_id, id DESC);
        """)
    logger.info(f"[db] База данных инициализирована: {DB_PATH}")


def get_mode(user_id: int) -> str:
    """Возвращает текущую роль пользователя (создаёт запись если нет)."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT mode FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row:
            return row[0]
        # Первый визит — создаём пользователя
        conn.execute(
            "INSERT INTO users(user_id) VALUES (?)", (user_id,)
        )
        return "assistant"


def set_mode(user_id: int, mode: str) -> None:
    """Сохраняет выбранную роль."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO users(user_id, mode) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET mode=excluded.mode,
                                               updated_at=datetime('now')
        """, (user_id, mode))


def add_message(user_id: int, role: str, content: str) -> None:
    """
    Добавляет сообщение в историю.
    Автоматически удаляет старые — храним только MAX_HISTORY_MESSAGES.
    """
    with sqlite3.connect(DB_PATH) as conn:
        # Убедимся что пользователь существует
        conn.execute(
            "INSERT OR IGNORE INTO users(user_id) VALUES (?)", (user_id,)
        )
        # Добавляем сообщение
        conn.execute(
            "INSERT INTO messages(user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        # Обрезаем старые сообщения — оставляем только последние N
        conn.execute("""
            DELETE FROM messages
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM messages
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            )
        """, (user_id, user_id, MAX_HISTORY_MESSAGES))


def get_history(user_id: int) -> list[dict]:
    """Возвращает историю сообщений в формате для OpenAI API."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT role, content FROM messages
            WHERE user_id = ?
            ORDER BY id ASC
        """, (user_id,)).fetchall()
    return [{"role": r[0], "content": r[1]} for r in rows]


def reset_history(user_id: int) -> None:
    """Очищает историю диалога (роль сохраняется)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM messages WHERE user_id = ?", (user_id,)
        )
    logger.info(f"[db] История пользователя {user_id} очищена")
