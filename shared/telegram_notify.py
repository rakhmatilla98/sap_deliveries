import os
import requests
import json
from shared.config import BOT_TOKEN, WEBAPP_URL
from shared.models import TelegramUser

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_telegram_delivery_image(
    user: TelegramUser,
    image_path: str,
    caption: str
):
    """
    Sends delivery image to Telegram user with WebApp button
    """

    if not os.path.exists(image_path):
        print("❌ Image not found:", image_path)
        return

    web_app_text = (
        "✅ Review & approve"
        if user.role == "approver"
        else "📦 View deliveries"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": web_app_text,
                    "web_app": {
                        "url": WEBAPP_URL
                    }
                }
            ]
        ]
    }

    try:
        with open(image_path, "rb") as img:
            response = requests.post(
                f"{TELEGRAM_API}/sendPhoto",
                data={
                    "chat_id": user.telegram_id,
                    "caption": caption,
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps(reply_markup)
                },
                files={
                    "photo": img
                },
                timeout=10
            )

        if not response.ok:
            print(
                "❌ Telegram sendPhoto failed:",
                response.status_code,
                response.text
            )

    except Exception as e:
        print("❌ Telegram notify error:", e)
