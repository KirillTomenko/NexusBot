"""
utils/llm.py — асинхронный клиент для запросов к LLM через ProxyAPI.
Использует SOCKS5-прокси Karing (localhost:3067) для работы в РФ.
"""
import logging
import httpx
from config import PROXY_API_KEY, PROXY_API_BASE, LLM_MODEL, SOCKS5_PROXY

logger = logging.getLogger(__name__)


def _make_client() -> httpx.AsyncClient:
    """Создаёт httpx-клиент с SOCKS5-прокси (если задан)."""
    kwargs = {"timeout": 60.0}
    if SOCKS5_PROXY:
        kwargs["proxy"] = SOCKS5_PROXY
        logger.debug(f"[llm] Используется прокси: {SOCKS5_PROXY}")
    return httpx.AsyncClient(**kwargs)


async def ask_llm(messages: list[dict]) -> dict:
    """
    Отправляет запрос к LLM и возвращает ответ.

    Args:
        messages: список сообщений [{"role": ..., "content": ...}]

    Returns:
        {"success": True, "content": "...", "usage": {...}}
        или
        {"success": False, "error": "..."}
    """
    headers = {
        "Authorization": f"Bearer {PROXY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "max_tokens": 1500,
    }

    try:
        async with _make_client() as client:
            response = await client.post(
                f"{PROXY_API_BASE}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return {"success": True, "content": content, "usage": usage}

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        logger.error(f"[LLM] HTTPStatusError: {error_msg}")
        return {"success": False, "error": error_msg}

    except Exception as e:
        logger.error(f"[LLM] Unexpected error: {e}")
        return {"success": False, "error": str(e)}
