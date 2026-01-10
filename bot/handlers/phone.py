from aiogram import types, F
from sqlalchemy.orm import Session

from shared.db import SessionLocal
from shared.models import TelegramUser
from bot.sap_bp import find_bp_by_phone, normalize_phone


async def phone_handler(message: types.Message):
    contact = message.contact

    if contact.user_id != message.from_user.id:
        await message.answer("❌ Send your own phone number")
        return

    phone = normalize_phone(contact.phone_number)

    db = SessionLocal()
    try:
        user = db.query(TelegramUser).filter(
            TelegramUser.telegram_id == message.from_user.id
        ).first()

        if not user:
            await message.answer("❌ Please use /start first")
            return

        user.phone_number = phone
        user.phone_verified = True
        user.is_active = False  # WAIT for BP sync

        db.commit()

    finally:
        db.close()

    await message.answer(
        "✅ Phone saved. Your account will be activated after verification."
    )
