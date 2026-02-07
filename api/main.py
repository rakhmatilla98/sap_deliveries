# api/main.py
import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi import Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload

from api.auth import get_current_user
from shared.config import BASE_DIR, HOST, PORT, API_STATIC_DIR
from shared.db import SessionLocal
from shared.models import Delivery, TelegramUser, Item, Order, OrderItem
from shared.schemas import DeliveryOut, HistoryOut, ItemOut, OrderIn

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
# Marketplace Endpoints
# -------------------------------------------------

@app.get("/api/items", response_model=list[ItemOut])
def get_items(
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Item).filter(Item.quantity > 0) # Only in stock?
    
    if q:
        query = query.filter(Item.item_name.ilike(f"%{q}%"))
        
    items = query.order_by(Item.updated_at.desc()).limit(limit).offset(offset).all()
    return items


@app.post("/api/orders")
def create_order(
    payload: OrderIn,
    user: TelegramUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
        
    # Calculate Total
    total_amount = 0.0
    order_items = []
    
    for cart_item in payload.items:
        db_item = db.query(Item).filter(Item.item_code == cart_item.item_code).first()
        if not db_item:
            continue # Skip invalid items or raise error
            
        line_total = db_item.price * cart_item.quantity
        total_amount += line_total
        
        order_items.append(OrderItem(
            item_code=db_item.item_code,
            item_name=db_item.item_name,
            quantity=cart_item.quantity,
            price=db_item.price,
            line_total=line_total
        ))
        
    if not order_items:
        raise HTTPException(status_code=400, detail="No valid items in order")
        
    # Create Order
    new_order = Order(
        telegram_id=user.telegram_id,
        card_code=user.card_code,
        card_name=user.card_name,
        doc_total=total_amount,
        items=order_items
    )
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    # Optional: Trigger sync immediately or let worker handle it
    # For now, let worker handle it via "new" status
    
    return {"status": "ok", "order_id": new_order.id}


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
@app.get("/api/today", response_model=list[DeliveryOut])
def get_today(
        user: TelegramUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    deliveries = (
        db.query(Delivery)
        .options(joinedload(Delivery.items))
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
@app.get("/api/history", response_model=HistoryOut)
def get_history(
    user: TelegramUser = Depends(get_current_user),
    db: Session = Depends(get_db),

    year: int | None = Query(None, ge=2000, le=2100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    query = db.query(Delivery).options(joinedload(Delivery.items)).filter(
        Delivery.card_code == user.card_code
    )

    if year:
        start = f"{year}-01-01"
        end = f"{year + 1}-01-01"

        query = query.filter(
            Delivery.date >= start,
            Delivery.date < end
        )

    total = query.count()

    deliveries = (
        query
        .order_by(Delivery.date.desc(), Delivery.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": deliveries
    }


# @app.get("/api/history")
# def get_history(
#         user: TelegramUser = Depends(get_current_user),
#         db: Session = Depends(get_db)
# ):
#     deliveries = (
#         db.query(Delivery)
#         .filter(
#             Delivery.card_code == user.card_code
#         )
#         .order_by(Delivery.date.desc(), Delivery.created_at.desc())
#         .all()
#     )
#     return deliveries


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
