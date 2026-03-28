from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from shared.db import SessionLocal
from shared.models import TelegramUser
from shared.translations import get_text

settings_router = Router()

def get_language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Рус", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇬🇧 Eng", callback_data="lang_en"),
            InlineKeyboardButton(text="🇺🇿 O'zb", callback_data="lang_uz")
        ]
    ])

@settings_router.message(F.text == "/settings")
async def settings_command(message: types.Message):
    db = SessionLocal()
    try:
        user = db.query(TelegramUser).filter(
            TelegramUser.telegram_id == message.from_user.id
        ).first()

        lang = user.language if user else "ru"
        
        await message.answer(
            get_text("settings_prompt", lang),
            reply_markup=get_language_keyboard()
        )
    finally:
        db.close()

@settings_router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback_query: types.CallbackQuery):
    lang_code = callback_query.data.split("_")[1]
    
    db = SessionLocal()
    try:
        user = db.query(TelegramUser).filter(
            TelegramUser.telegram_id == callback_query.from_user.id
        ).first()

        if user:
            user.language = lang_code
            db.commit()
            
            await callback_query.message.edit_text(
                get_text("language_changed", lang_code),
                reply_markup=None
            )
        else:
            await callback_query.answer("User not found.", show_alert=True)
            
    finally:
        db.close()
