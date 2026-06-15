"""
Telegram-бот ДивиБонд.

Минимальная обязанность бота — открыть мини-приложение по кнопке.
Вся логика (списки, фильтры, карточки) реализована в frontend + backend API.

Настройка:
  1. Получите токен бота у @BotFather (команда /newbot).
  2. В @BotFather выполните /mybots → выбрать бота → Bot Settings → Menu Button
     → Configure Menu Button → укажите тот же URL, что и WEBAPP_URL ниже
     (HTTPS, например https://your-domain.example/divibond/).
  3. Экспортируйте переменные окружения и запустите:

       export BOT_TOKEN="7355548334:AAErpHENllaTpnbH4p9TOOAFoHwXcESQ0E4"
       export WEBAPP_URL="https://your-domain.example/divibond/"
       python3 bot.py

Зависимости: pip install aiogram
"""

import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7355548334:AAErpHENllaTpnbH4p9TOOAFoHwXcESQ0E4")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://your-domain.example/divibond/")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📊 Открыть ДивиБонд", web_app=WebAppInfo(url=WEBAPP_URL)),
    ]])
    await message.answer(
        "Привет! ДивиБонд помогает находить облигации и дивидендные акции "
        "Московской биржи со стабильной доходностью.\n\n"
        "— текущая доходность облигаций считается от актуальной цены;\n"
        "— дивидендная доходность акций — по факту выплат за прошлый год;\n"
        "— можно фильтровать по доходности, цене и сроку до погашения.\n\n"
        "Нажмите кнопку ниже, чтобы открыть приложение.",
        reply_markup=keyboard,
    )


@dp.message()
async def fallback(message: Message) -> None:
    # На любое другое сообщение — напоминаем про /start.
    await message.answer("Введите /start, чтобы открыть приложение ДивиБонд.")


async def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("Переменная окружения BOT_TOKEN не задана")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
