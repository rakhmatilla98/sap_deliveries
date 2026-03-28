from aiogram import types, F
from sqlalchemy.orm import Session

from shared.db import SessionLocal
from shared.models import TelegramUser
from bot.sap_bp import find_bp_by_phone, normalize_phone
from shared.translations import get_text


async def phone_handler(message: types.Message):
    contact = message.contact

    db = SessionLocal()
    user = db.query(TelegramUser).filter(TelegramUser.telegram_id == message.from_user.id).first()
    lang = user.language if user else "ru"

    if contact.user_id != message.from_user.id:
        await message.answer(get_text("error_own_phone", lang))
        return

    phone = normalize_phone(contact.phone_number)
    try:
        if not user:
            await message.answer(get_text("error_start_first", lang))
            return

        user.phone_number = phone
        user.phone_verified = True
        user.is_active = False  # WAIT for BP sync

        db.commit()

    finally:
        db.close()

    await message.answer(
        get_text("phone_saved", lang)
    )
