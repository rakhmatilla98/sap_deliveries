from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from shared.db import SessionLocal
from shared.models import TelegramUser


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> TelegramUser:

    telegram_id = request.headers.get("X-Telegram-User-Id")

    if not telegram_id:
        raise HTTPException(status_code=401, detail="Missing Telegram ID")

    user = db.query(TelegramUser).filter(
        TelegramUser.telegram_id == int(telegram_id),
        TelegramUser.is_active == True,
        TelegramUser.phone_verified == True
    ).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="Access denied")

    return user
