from aiogram import types

from bot.keyboards import phone_keyboard, webapp_keyboard
from shared.db import SessionLocal
from shared.models import TelegramUser


async def start_handler(message: types.Message):
    db = SessionLocal()
    try:
        user = db.query(TelegramUser).filter(
            TelegramUser.telegram_id == message.from_user.id
        ).first()

        # ------------------------------
        # New user → create + ask phone
        # ------------------------------
        if not user:
            user = TelegramUser(
                telegram_id=message.from_user.id,
                is_active=False,
                phone_verified=False
            )
            db.add(user)
            db.commit()

            await message.answer(
                "Welcome 👋\nPlease share your phone number to continue.",
                reply_markup=phone_keyboard
            )
            return

        # ------------------------------
        # Existing but NOT verified
        # ------------------------------
        if not user.phone_verified:
            await message.answer(
                "Please share your phone number to continue.",
                reply_markup=phone_keyboard
            )
            return

        # ------------------------------
        # Verified but waiting for SAP
        # ------------------------------
        if not user.is_active:
            await message.answer(
                "⏳ Your account is pending verification.\n"
                "You will get access shortly after confirmation."
            )
            return

        # ------------------------------
        # Fully active → show WebApp
        # ------------------------------
        await message.answer(
            "✅ Access granted.\nOpen the delivery panel:",
            reply_markup=webapp_keyboard
        )

    finally:
        db.close()
