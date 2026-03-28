from aiogram import types

from bot.keyboards import get_phone_keyboard, get_webapp_keyboard
from shared.db import SessionLocal
from shared.models import TelegramUser
from shared.translations import get_text


async def start_handler(message: types.Message):
    db = SessionLocal()
    try:
        user = db.query(TelegramUser).filter(
            TelegramUser.telegram_id == message.from_user.id
        ).first()

        lang = user.language if hasattr(user, 'language') else "ru"
        # ------------------------------
        # New user → create + ask phone
        # ------------------------------
        if not user or not hasattr(user, 'phone_verified') or getattr(user, 'phone_verified') is None: # Quick fallback checks
            if not user:
                user = TelegramUser(
                    telegram_id=message.from_user.id,
                    is_active=False,
                    phone_verified=False,
                    language="ru"
                )
                db.add(user)
                db.commit()

            await message.answer(
                get_text("welcome_phone", "ru"),
                reply_markup=get_phone_keyboard("ru")
            )
            return

        # ------------------------------
        # Existing but NOT verified
        # ------------------------------
        if not user.phone_verified:
            await message.answer(
                get_text("request_phone", lang),
                reply_markup=get_phone_keyboard(lang)
            )
            return

        # ------------------------------
        # Verified but waiting for SAP
        # ------------------------------
        if not user.is_active:
            await message.answer(
                get_text("waiting_activation", lang)
            )
            return

        # ------------------------------
        # Fully active → show WebApp
        # ------------------------------
        await message.answer(
            get_text("open_panel", lang),
            reply_markup=get_webapp_keyboard(lang)
        )

    finally:
        db.close()
