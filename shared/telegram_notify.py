import requests
from shared.config import BOT_TOKEN, WEBAPP_URL

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_telegram_message(chat_id: int, text: str):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": "📦 Open deliveries",
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
