import requests
from shared.config import BOT_TOKEN, WEBAPP_URL
from shared.models import TelegramUser

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_telegram_message(user: TelegramUser, text: str):
    web_app_text = (
        "✅ Review & approve"
        if user.role == "approver"
        else "📦 View deliveries"
    )

    payload = {
        "chat_id": user.telegram_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
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
    }

    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json=payload,
            timeout=5
        )
    except Exception as e:
        print("Telegram notify error:", e)
