"""
main.py — точка входа NexusBot.
Telegram-бот с персистентной LLM-памятью, ролями и генерацией видео.
"""

import asyncio
import logging
import json
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import BOT_TOKEN
from db import init_db, get_mode, set_mode, add_message, get_history, reset_history
from utils.llm import ask_llm
from utils.video import generate_video
from utils.cost import estimate_cost, get_usd_rub_rate

# ─── Логирование ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Инициализация ─────────────────────────────────────────────────────────────
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

with open("prompts.json", encoding="utf-8") as f:
    PROMPTS_DATA = json.load(f)


# ─── /start ────────────────────────────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    mode_key = get_mode(user_id)
    mode_name = PROMPTS_DATA["prompts"][mode_key]["name"]
    logger.info(f"[/start] user_id={user_id}")
    await message.answer(
        f"👋 Привет! Я *NexusBot* — AI-консультант с долгосрочной памятью.\n\n"
        f"🎭 Текущая роль: *{mode_name}*\n\n"
        f"Команды:\n"
        f"/mode — сменить роль\n"
        f"/reset — очистить историю\n"
        f"/video — сгенерировать AI-видео\n\n"
        f"Просто напиши мне что-нибудь 💬",
        parse_mode="Markdown",
    )


# ─── /reset ────────────────────────────────────────────────────────────────────

@dp.message(Command("reset"))
async def cmd_reset(message: Message):
    user_id = message.from_user.id
    reset_history(user_id)
    logger.info(f"[/reset] user_id={user_id}")
    await message.answer("🗑 История диалога очищена. Начнём заново!")


# ─── /mode ─────────────────────────────────────────────────────────────────────

@dp.message(Command("mode"))
async def cmd_mode(message: Message):
    user_id = message.from_user.id
    current_mode = get_mode(user_id)
    buttons = []
    for key, data in PROMPTS_DATA["prompts"].items():
        marker = "✅ " if key == current_mode else ""
        buttons.append([InlineKeyboardButton(
            text=f"{marker}{data['name']} — {data['description']}",
            callback_data=f"mode:{key}"
        )])
    await message.answer(
        "🎭 Выбери роль ассистента:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@dp.callback_query(lambda c: c.data.startswith("mode:"))
async def handle_mode_select(callback: CallbackQuery):
    user_id = callback.from_user.id
    mode_key = callback.data.split(":", 1)[1]
    if mode_key not in PROMPTS_DATA["prompts"]:
        await callback.answer("Неизвестный режим.", show_alert=True)
        return
    set_mode(user_id, mode_key)
    reset_history(user_id)
    mode_name = PROMPTS_DATA["prompts"][mode_key]["name"]
    logger.info(f"[mode] user_id={user_id} → {mode_key}")
    await callback.message.edit_text(
        f"✅ Роль: *{mode_name}*\n_История очищена_\n\n"
        f"{PROMPTS_DATA['prompts'][mode_key]['description']}",
        parse_mode="Markdown",
    )
    await callback.answer()


# ─── /video ────────────────────────────────────────────────────────────────────

@dp.message(Command("video"))
async def cmd_video(message: Message):
    user_id = message.from_user.id
    prompt_text = message.text.replace("/video", "").strip()
    if not prompt_text:
        await message.answer(
            "🎬 Укажи промпт после команды:\n"
            "`/video A cat walking on a beach at sunset`",
            parse_mode="Markdown",
        )
        return
    logger.info(f"[/video] user_id={user_id}, промпт: {prompt_text[:80]}")
    status_msg = await message.answer("⏳ Генерирую видео... ~1–2 минуты.")
    result = await generate_video(prompt_text)
    if result["success"]:
        await status_msg.edit_text(
            f"✅ Видео готово!\n\n"
            f"🔗 [Скачать]({result['url']})\n"
            f"⏱ {result.get('duration', 4)} сек · 💰 ~{result.get('cost_rub', '?')} ₽",
            parse_mode="Markdown",
        )
    else:
        await status_msg.edit_text(f"❌ Ошибка: `{result['error']}`", parse_mode="Markdown")


# ─── Основной обработчик сообщений ─────────────────────────────────────────────

@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    user_text = (message.text or "").strip()
    if not user_text:
        return

    logger.info(f"[msg] user_id={user_id}: {user_text[:60]}")
    add_message(user_id, "user", user_text)

    mode_key = get_mode(user_id)
    system_prompt = PROMPTS_DATA["prompts"][mode_key]["system_prompt"]
    history = get_history(user_id)
    messages = [{"role": "system", "content": system_prompt}] + history

    typing_msg = await message.answer("⌨️")
    response = await ask_llm(messages)

    if response["success"]:
        reply_text = response["content"]
        usage = response.get("usage", {})
        usd_rub = await get_usd_rub_rate()
        cost = estimate_cost(usage, usd_rub)

        add_message(user_id, "assistant", reply_text)

        logger.info(
            f"[LLM] user_id={user_id} | роль={mode_key} | "
            f"in={usage.get('prompt_tokens',0)} out={usage.get('completion_tokens',0)} | "
            f"${cost['usd']:.5f} (~{cost['rub']:.2f} ₽)"
        )

        cost_line = (
            f"\n\n💰 _{usage.get('prompt_tokens',0)} вх / "
            f"{usage.get('completion_tokens',0)} исх · "
            f"~{cost['rub']:.2f} ₽_"
        )
        await typing_msg.edit_text(reply_text + cost_line, parse_mode="Markdown")
    else:
        logger.error(f"[LLM error] {response['error']}")
        await typing_msg.edit_text(f"❌ {response['error']}")


# ─── Запуск ────────────────────────────────────────────────────────────────────

async def main():
    init_db()
    logger.info("🚀 NexusBot запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
