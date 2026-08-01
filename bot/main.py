import asyncio
import os
import sys
from aiogram import Bot, Dispatcher, F
from dotenv import load_dotenv

# Ensure UTF-8 output when running as a Windows service
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from bot.handlers.start import start_handler
from bot.handlers.phone import phone_handler
from bot.handlers.settings import settings_router

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.message.register(start_handler, F.text == "/start")
    dp.message.register(phone_handler, F.contact)
    dp.include_router(settings_router)

    print("🤖 Bot started (polling)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
