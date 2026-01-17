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
                "Добро пожаловать 👋\nПожалуйста, поделитесь своим номером телефона, чтобы продолжить.",
                reply_markup=phone_keyboard
            )
            return

        # ------------------------------
        # Existing but NOT verified
        # ------------------------------
        if not user.phone_verified:
            await message.answer(
                "Пожалуйста, поделитесь своим номером телефона, чтобы продолжить.",
                reply_markup=phone_keyboard
            )
            return

        # ------------------------------
        # Verified but waiting for SAP
        # ------------------------------
        if not user.is_active:
            await message.answer(
                "⏳ Ваш аккаунт ожидает подтверждения.\n"
                "Вы получите доступ вскоре после подтверждения."
            )
            return

        # ------------------------------
        # Fully active → show WebApp
        # ------------------------------
        await message.answer(
            "✅ Откройте панель отгрузок:",
            reply_markup=webapp_keyboard
        )

    finally:
        db.close()
