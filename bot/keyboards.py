from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from shared.config import WEBAPP_URL

phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Share phone number", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

webapp_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Открыть Отгрузки",
                              web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
