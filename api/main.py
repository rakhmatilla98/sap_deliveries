# api/main.py
import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi import Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload

from api.auth import get_current_user
from shared.config import BASE_DIR, HOST, PORT, API_STATIC_DIR, DATA_DIR
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
app.mount(
    "/data",
    StaticFiles(directory=DATA_DIR),
    name="data"
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
    query = db.query(Item).options(joinedload(Item.images)).filter(Item.quantity > 0) # Only in stock?
    
    if q:
        query = query.filter(Item.item_name.ilike(f"%{q}%"))
        
    items = query.order_by(Item.updated_at.desc()).limit(limit).offset(offset).all()
    
    # Populate image_url
    for item in items:
        if item.images:
            # Pick primary or first
            primary_img = next((img for img in item.images if img.is_primary), item.images[0])
            path = primary_img.file_path.replace("\\", "/")
            if not path.startswith("/"):
                path = "/" + path
            item.image_url = path
            
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
# Cart Endpoints (Server-side persistence)
# -------------------------------------------------

@app.get("/api/cart", response_model=list)
def get_cart(
    user: TelegramUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's cart with full item details"""
    from shared.models import Cart
    from shared.schemas import CartItemOut
    
    cart_items = db.query(Cart).filter(Cart.telegram_id == user.telegram_id).all()
    
    result = []
    for cart_item in cart_items:
        db_item = db.query(Item).filter(Item.item_code == cart_item.item_code).first()
        if not db_item:
            continue  # Skip if item no longer exists
        
        # Get image URL
        image_url = None
        if db_item.images:
            primary_img = next((img for img in db_item.images if img.is_primary), db_item.images[0])
            path = primary_img.file_path.replace("\\", "/")
            if not path.startswith("/"):
                path = "/" + path
            image_url = path
        
        result.append({
            "item_code": db_item.item_code,
            "item_name": db_item.item_name,
            "quantity": cart_item.quantity,
            "price": db_item.price,
            "currency": db_item.currency,
            "image_url": image_url,
            "line_total": db_item.price * cart_item.quantity
        })
    
    return result


@app.post("/api/cart/add")
def add_to_cart(
    cart_in: dict,
    user: TelegramUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add item to cart or increment quantity if exists"""
    from shared.models import Cart
    
    item_code = cart_in.get("item_code")
    quantity = cart_in.get("quantity", 1)
    
    if not item_code:
        raise HTTPException(status_code=400, detail="item_code required")
    
    # Check if item exists
    db_item = db.query(Item).filter(Item.item_code == item_code).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if already in cart
    cart_item = db.query(Cart).filter(
        Cart.telegram_id == user.telegram_id,
        Cart.item_code == item_code
    ).first()
    
    if cart_item:
        # Increment quantity
        cart_item.quantity += quantity
    else:
        # Create new cart item
        cart_item = Cart(
            telegram_id=user.telegram_id,
            item_code=item_code,
            quantity=quantity
        )
        db.add(cart_item)
    
    db.commit()
    return {"status": "ok", "quantity": cart_item.quantity}


@app.put("/api/cart/update/{item_code}")
def update_cart_item(
    item_code: str,
    update_in: dict,
    user: TelegramUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update cart item quantity"""
    from shared.models import Cart
    
    quantity = update_in.get("quantity")
    if quantity is None:
        raise HTTPException(status_code=400, detail="quantity required")
    
    cart_item = db.query(Cart).filter(
        Cart.telegram_id == user.telegram_id,
        Cart.item_code == item_code
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Item not in cart")
    
    if quantity <= 0:
        # Remove item
        db.delete(cart_item)
    else:
        cart_item.quantity = quantity
    
    db.commit()
    return {"status": "ok"}


@app.delete("/api/cart/remove/{item_code}")
def remove_from_cart(
    item_code: str,
    user: TelegramUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove item from cart"""
    from shared.models import Cart
    
    cart_item = db.query(Cart).filter(
        Cart.telegram_id == user.telegram_id,
        Cart.item_code == item_code
    ).first()
    
    if cart_item:
        db.delete(cart_item)
        db.commit()
    
    return {"status": "ok"}


@app.delete("/api/cart/clear")
def clear_cart(
    user: TelegramUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all items from user's cart"""
    from shared.models import Cart
    
    db.query(Cart).filter(Cart.telegram_id == user.telegram_id).delete()
    db.commit()
    
    return {"status": "ok"}



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
