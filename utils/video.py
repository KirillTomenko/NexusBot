"""
utils/video.py — генерация видео через ProxyAPI (Sora 2).
Использует SOCKS5-прокси Karing (localhost:3067).

Алгоритм:
1. POST /videos/generations — запускаем задачу, получаем task_id
2. Polling GET /videos/generations/{task_id} — ждём завершения
3. Возвращаем URL готового видео
"""
import asyncio
import logging
import httpx
from config import PROXY_API_KEY, VIDEO_MODEL, VIDEO_DURATION, SOCKS5_PROXY

logger = logging.getLogger(__name__)

VIDEO_API_BASE = "https://api.proxyapi.ru/openai/v1"

PRICE_PER_SEC = {
    "sora-2": 27,
    "veo-3-fast": 43,
    "veo-3-1": 95,
}


def _make_client(timeout: float = 30.0) -> httpx.AsyncClient:
    """Создаёт httpx-клиент с SOCKS5-прокси (если задан)."""
    kwargs = {"timeout": timeout}
    if SOCKS5_PROXY:
        kwargs["proxy"] = SOCKS5_PROXY
    return httpx.AsyncClient(**kwargs)


async def generate_video(prompt: str) -> dict:
    """
    Запускает генерацию видео и возвращает ссылку.

    Returns:
        {"success": True, "url": "...", "duration": 4, "cost_rub": 108}
        или
        {"success": False, "error": "..."}
    """
    headers = {
        "Authorization": f"Bearer {PROXY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": VIDEO_MODEL,
        "prompt": prompt,
        "duration": VIDEO_DURATION,
    }

    try:
        async with _make_client() as client:
            logger.info(f"[video] Запуск: модель={VIDEO_MODEL}, duration={VIDEO_DURATION}s")
            resp = await client.post(
                f"{VIDEO_API_BASE}/videos/generations",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            task_data = resp.json()

        task_id = task_data.get("id")
        if not task_id:
            return {"success": False, "error": f"Не получен task_id: {task_data}"}

        logger.info(f"[video] task_id={task_id}, ожидаем...")

        for attempt in range(60):
            await asyncio.sleep(5)
            async with _make_client() as client:
                status_resp = await client.get(
                    f"{VIDEO_API_BASE}/videos/generations/{task_id}",
                    headers=headers,
                )
                status_resp.raise_for_status()
                status_data = status_resp.json()

            status = status_data.get("status", "")
            logger.info(f"[video] attempt={attempt+1}, status={status}")

            if status == "completed":
                video_url = (
                    status_data.get("url")
                    or status_data.get("video_url")
                    or status_data.get("result", {}).get("url")
                    or status_data.get("data", [{}])[0].get("url", "")
                )
                cost_rub = PRICE_PER_SEC.get(VIDEO_MODEL, 27) * VIDEO_DURATION
                logger.info(f"[video] Готово! cost={cost_rub}₽")
                return {"success": True, "url": video_url, "duration": VIDEO_DURATION, "cost_rub": cost_rub}

            if status in ("failed", "error"):
                error_msg = status_data.get("error", {}).get("message", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}

        return {"success": False, "error": "Таймаут: видео не сгенерировано за 5 минут"}

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text[:300]}"
        logger.error(f"[video] HTTPStatusError: {error_msg}")
        return {"success": False, "error": error_msg}

    except Exception as e:
        logger.error(f"[video] Unexpected error: {e}")
        return {"success": False, "error": str(e)}
