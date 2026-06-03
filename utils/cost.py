"""
utils/cost.py — расчёт стоимости LLM-запроса в рублях.
Курс USD/RUB получаем с API Центрального банка РФ.
"""
import logging
import httpx
from config import COST_INPUT_PER_1M, COST_OUTPUT_PER_1M

logger = logging.getLogger(__name__)

# Резервный курс на случай недоступности API ЦБ
FALLBACK_USD_RUB = 90.0


async def get_usd_rub_rate() -> float:
    """
    Получает актуальный курс USD/RUB с API Центрального банка РФ.
    При ошибке возвращает резервный курс FALLBACK_USD_RUB.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://www.cbr-xml-daily.ru/daily_json.js")
            resp.raise_for_status()
            data = resp.json()
            rate = data["Valute"]["USD"]["Value"]
            logger.debug(f"[cost] Курс ЦБ: 1 USD = {rate} ₽")
            return float(rate)
    except Exception as e:
        logger.warning(f"[cost] Не удалось получить курс ЦБ: {e}. Используем {FALLBACK_USD_RUB}")
        return FALLBACK_USD_RUB


def estimate_cost(usage: dict, usd_rub: float = FALLBACK_USD_RUB) -> dict:
    """
    Рассчитывает стоимость запроса на основе токенов.

    Args:
        usage: {"prompt_tokens": int, "completion_tokens": int}
        usd_rub: курс доллара к рублю

    Returns:
        {"usd": float, "rub": float}
    """
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)

    cost_usd = (
        input_tokens / 1_000_000 * COST_INPUT_PER_1M
        + output_tokens / 1_000_000 * COST_OUTPUT_PER_1M
    )
    cost_rub = cost_usd * usd_rub

    return {"usd": cost_usd, "rub": cost_rub}
