import asyncio
import os
from aiogram import Bot, Dispatcher, F
from dotenv import load_dotenv

from bot.handlers.start import start_handler
from bot.handlers.phone import phone_handler

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.message.register(start_handler, F.text == "/start")
    dp.message.register(phone_handler, F.contact)

    print("🤖 Bot started (polling)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
