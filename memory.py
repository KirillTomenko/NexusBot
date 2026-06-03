"""
memory.py — менеджер памяти диалогов.
Хранит историю сообщений и выбранную роль для каждого пользователя.
Данные хранятся в оперативной памяти (dict).
"""
from collections import deque
from typing import Literal
from config import MAX_HISTORY_MESSAGES

# Роль по умолчанию совпадает с "default_prompt" в prompts.json
DEFAULT_MODE = "assistant"


class MemoryManager:
    """
    Управляет контекстом диалога для каждого пользователя.
    
    Структура:
        _users = {
            user_id: {
                "mode": "assistant",          # текущая роль
                "history": deque([            # последние N сообщений
                    {"role": "user", "content": "..."},
                    {"role": "assistant", "content": "..."},
                ])
            }
        }
    """

    def __init__(self):
        self._users: dict = {}

    def init_user(self, user_id: int) -> None:
        """Инициализирует запись для нового пользователя (если ещё нет)."""
        if user_id not in self._users:
            self._users[user_id] = {
                "mode": DEFAULT_MODE,
                "history": deque(maxlen=MAX_HISTORY_MESSAGES),
            }

    def get_mode(self, user_id: int) -> str:
        """Возвращает текущую роль пользователя."""
        self.init_user(user_id)
        return self._users[user_id]["mode"]

    def set_mode(self, user_id: int, mode_key: str) -> None:
        """Устанавливает роль пользователя."""
        self.init_user(user_id)
        self._users[user_id]["mode"] = mode_key

    def add_message(self, user_id: int, role: Literal["user", "assistant"], content: str) -> None:
        """Добавляет сообщение в историю (автоматически обрезает старые)."""
        self.init_user(user_id)
        self._users[user_id]["history"].append({"role": role, "content": content})

    def get_history(self, user_id: int) -> list[dict]:
        """Возвращает историю сообщений как список для передачи в API."""
        self.init_user(user_id)
        return list(self._users[user_id]["history"])

    def reset_history(self, user_id: int) -> None:
        """Очищает историю диалога (не трогает режим)."""
        self.init_user(user_id)
        self._users[user_id]["history"].clear()
