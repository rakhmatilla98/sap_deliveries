# api/main.py
import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles

from api.auth import get_current_user
from shared.config import BASE_DIR, HOST, PORT, API_STATIC_DIR
from shared.db import SessionLocal
from shared.models import Delivery, TelegramUser

app = FastAPI(title="Delivery API")
STATIC_DIR = os.path.join(BASE_DIR, "api", "static")
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


# -------------------------------------------------
# Database dependency
# -------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------------------------
# Health check
# -------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# Routes
@app.get("/")
def index():
    return FileResponse(API_STATIC_DIR / "index.html")


# -------------------------------------------------
# Get unapproved deliveries (Today / New)
# -------------------------------------------------
@app.get("/api/today")
def get_today(
        user: TelegramUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    deliveries = (
        db.query(Delivery)
        .filter(
            Delivery.approved == False,
            Delivery.card_code == user.card_code
        )
        .order_by(Delivery.date.desc(), Delivery.created_at.desc())
        .all()
    )
    return deliveries


# -------------------------------------------------
# Get all deliveries (History)
# -------------------------------------------------
@app.get("/api/history")
def get_history(
        user: TelegramUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    deliveries = (
        db.query(Delivery)
        .filter(
            Delivery.card_code == user.card_code
        )
        .order_by(Delivery.date.desc(), Delivery.created_at.desc())
        .all()
    )
    return deliveries


# -------------------------------------------------
# Approve delivery
# -------------------------------------------------
@app.post("/api/approve/{delivery_id}")
def approve_delivery(
        delivery_id: int,
        user: TelegramUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if user.role != "approver":
        raise HTTPException(status_code=403, detail="Not allowed")

    delivery = (
        db.query(Delivery)
        .filter(
            Delivery.id == delivery_id,
            Delivery.card_code == user.card_code
        )
        .first()
    )

    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    if delivery.approved:
        return {"status": "already approved"}

    delivery.approved = True
    db.commit()

    return {"status": "ok"}


# Entry point
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host=HOST, port=PORT, reload=False)
