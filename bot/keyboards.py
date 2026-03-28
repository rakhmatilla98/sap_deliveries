from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from shared.config import WEBAPP_URL
from shared.translations import get_text

def get_phone_keyboard(lang: str = "ru"):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text("btn_share_phone", lang), request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_webapp_keyboard(lang: str = "ru"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("btn_open_panel", lang),
                              web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
