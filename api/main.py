# api/main.py
import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi import Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from api.auth import get_current_user
from shared.config import BASE_DIR, HOST, PORT, API_STATIC_DIR, DATA_DIR
from shared.db import SessionLocal
from shared.models import Delivery, TelegramUser, Item, ItemCategory, Order, OrderItem
from shared.schemas import DeliveryOut, HistoryOut, ItemOut, OrderIn, ItemCategoryOut, ItemCategoryIn, ItemCategoryUpdate

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
        category_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
        db: Session = Depends(get_db)
):
    query = db.query(Item).options(joinedload(Item.images), joinedload(Item.category)).filter(Item.quantity > 0)

    if q:
        query = query.filter(func.lower(Item.item_name).contains(q.lower()))

    if category_id is not None:
        query = query.filter(Item.category_id == category_id)

    items = query.order_by(Item.updated_at.desc()).limit(limit).offset(offset).all()

    # Populate image_url and image_urls
    for item in items:
        if item.images:
            # Sort all images: primary first, then by file_path alphabetically (seq order)
            sorted_imgs = sorted(item.images, key=lambda img: (not img.is_primary, img.file_path))
            # Primary or first for backwards-compatible single image_url
            primary_img = sorted_imgs[0]
            path = primary_img.file_path.replace("\\", "/")
            if not path.startswith("/"):
                path = "/" + path
            item.image_url = path
            # All images list
            all_paths = []
            for img in sorted_imgs:
                p = img.file_path.replace("\\", "/")
                if not p.startswith("/"):
                    p = "/" + p
                all_paths.append(p)
            item.image_urls = all_paths

    return items


@app.get("/api/items/{item_code}", response_model=ItemOut)
def get_item(
        item_code: str,
        db: Session = Depends(get_db)
):
    item = db.query(Item).options(joinedload(Item.images), joinedload(Item.category)).filter(Item.item_code == item_code).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.images:
        sorted_imgs = sorted(item.images, key=lambda img: (not img.is_primary, img.file_path))
        primary_img = sorted_imgs[0]
        path = primary_img.file_path.replace("\\", "/")
        if not path.startswith("/"):
            path = "/" + path
        item.image_url = path
        item.image_urls = ["/" + img.file_path.replace("\\", "/").lstrip("/") for img in sorted_imgs]
    else:
        item.image_urls = []
    
    return item


# -------------------------------------------------
# Item Category Endpoints
# -------------------------------------------------

@app.get("/api/categories", response_model=list[ItemCategoryOut])
def get_categories(db: Session = Depends(get_db)):
    """Return all item categories ordered by sort_order."""
    return db.query(ItemCategory).order_by(ItemCategory.sort_order, ItemCategory.name).all()


@app.post("/api/categories", response_model=ItemCategoryOut, status_code=201)
def create_category(data: ItemCategoryIn, db: Session = Depends(get_db)):
    """Create a new item category."""
    existing = db.query(ItemCategory).filter(func.lower(ItemCategory.name) == data.name.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Category with this name already exists")
    category = ItemCategory(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@app.patch("/api/categories/{category_id}", response_model=ItemCategoryOut)
def update_category(category_id: int, data: ItemCategoryIn, db: Session = Depends(get_db)):
    """Update an existing category."""
    category = db.query(ItemCategory).filter(ItemCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


@app.delete("/api/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Delete a category. Items in this category will have their category set to NULL."""
    category = db.query(ItemCategory).filter(ItemCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()


@app.put("/api/items/{item_code}/category")
def update_item_category(item_code: str, category_id: int | None = None, db: Session = Depends(get_db)):
    """Set or clear the category for a specific item."""
    item = db.query(Item).filter(Item.item_code == item_code).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if category_id is not None:
        category = db.query(ItemCategory).filter(ItemCategory.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    item.category_id = category_id
    db.commit()
    return {"status": "success", "item_code": item_code, "category_id": category_id}


@app.post("/api/items/bulk-category")
def bulk_update_item_category(data: ItemCategoryUpdate, db: Session = Depends(get_db)):
    """Set the category for multiple items at once."""
    if data.category_id is not None:
        category = db.query(ItemCategory).filter(ItemCategory.id == data.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    db.query(Item).filter(Item.item_code.in_(data.item_codes)).update(
        {Item.category_id: data.category_id},
        synchronize_session=False
    )
    db.commit()
    return {"status": "success", "count": len(data.item_codes)}



import json
import platformdirs
import platformdirs
from google import genai
from google.genai import types
from fastapi import UploadFile, File, Form


@app.post("/api/scan-order")
async def scan_order(
        file: UploadFile = File(...),
        user: TelegramUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    print("--- SCAN ORDER ENDPOINT HIT ---")
    print(f"User: {user.telegram_id}, File: {file.filename}, Content-Type: {file.content_type}")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not configured.")
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured. Contact admin.")

    print("Configuring Gemini Client...")
    client = genai.Client(api_key=api_key)

    try:
        contents = await file.read()
        print(f"File read successfully. Size: {len(contents)} bytes.")
    except Exception as e:
        print(f"ERROR reading file: {e}")
        raise HTTPException(status_code=400, detail="Could not read file")

    items = db.query(Item).filter(Item.quantity > 0).all()
    # Create product list context
    product_catalog = "\n".join([f"- {item.item_code}: {item.item_name}" for item in items])

    prompt = f"""
You are an expert OCR and order entry assistant.
The user has uploaded an image of a handwritten or printed order.
Here is the current catalog of available products (item_code: item_name):
{product_catalog}

Your task is to:
1. Read the text from the image carefully.
2. For each ordered item found in the image, perform a fuzzy match against the catalog to find the exact `item_code` and `item_name`.
3. Extract the quantity requested. If no quantity is specified, assume 1.
4. Return the result STRICTLY as a JSON object with a single key "items" containing a list of objects. Each object must have "item_code", "item_name", and "quantity".
Example output:
{{
  "items": [
    {{"item_code": "P001", "item_name": "Product A", "quantity": 2}},
    {{"item_code": "P002", "item_name": "Product B", "quantity": 1}}
  ]
}}
If no items can be matched, return {{"items": []}}.
Do not include any markdown formatting (like ```json), just the raw JSON string.
"""

    try:
        # Uploading file using GenAI file API for parsing
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                prompt,
                types.Part.from_bytes(data=contents, mime_type=file.content_type)
            ]
        )

        response_text = response.text.strip()

        # Clean up markdown if model still included it
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        result_json = json.loads(response_text)

        matched_items = []
        for parsed_item in result_json.get("items", []):
            db_item = db.query(Item).filter(Item.item_code == parsed_item["item_code"]).first()
            if db_item:
                matched_items.append({
                    "item_code": db_item.item_code,
                    "item_name": db_item.item_name,
                    "quantity": parsed_item["quantity"],
                    "price": db_item.price
                })

        return {"items": matched_items}

    except json.JSONDecodeError:
        print(f"Failed to parse Gemini output: {response_text}")
        raise HTTPException(status_code=500, detail="Invalid format returned from AI model.")
    except Exception as e:
        print(f"Gemini API Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process image with AI: {str(e)}")


@app.post("/api/ai-chat")
async def process_ai_chat(
        text: str = Form(None),
        voice: UploadFile = File(None),
        user: TelegramUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    print("--- AI CHAT ENDPOINT HIT ---")
    if not text and not voice:
        raise HTTPException(status_code=400, detail="Need text or voice input")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY missing")

    client = genai.Client(api_key=api_key)

    items = db.query(Item).filter(Item.quantity > 0).all()
    product_catalog = "\n".join([f"- {item.item_code}: {item.item_name} | Price: {item.price} {item.currency}" for item in items])

    prompt = f"""
You are an expert AI sales assistant for a hardware/product store.
The user is talking to you and looking for products.
Here is the current catalog of available products (item_code: item_name | Price):
{product_catalog}

Your task is to:
1. Understand the user's request (which might be provided as text or audio).
2. Find the best matching products from the catalog that fulfill their need.
3. Come up with a friendly, helpful reply text. For example, if they ask for prices or cheapest options, respond accordingly.
4. Return the result STRICTLY as a JSON object with two keys:
   - "replyText": Your conversational reply as a string.
   - "items": A list of matched "item_code" strings. (Empty list if no matches).

Example output:
{{
  "replyText": "Here are some steel bolts I found for you:",
  "items": ["P001", "P005"]
}}
Do not include any markdown formatting (like ```json), just the raw JSON string.
"""

    contents = [prompt]
    if text:
        contents.append(text)
    if voice:
        try:
            voice_bytes = await voice.read()
            contents.append(types.Part.from_bytes(data=voice_bytes, mime_type=voice.content_type))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read voice data: {str(e)}")

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )

        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        result_json = json.loads(response_text.strip())

        reply_text = result_json.get("replyText", "Here is what I found:")
        item_codes = result_json.get("items", [])

        matched_items = []
        for code in item_codes:
            db_item = db.query(Item).filter(Item.item_code == code).first()
            if db_item:
                matched_items.append({
                    "item_code": db_item.item_code,
                    "item_name": db_item.item_name,
                    "price": db_item.price,
                    "currency": db_item.currency
                })

        return {"replyText": reply_text, "items": matched_items}

    except json.JSONDecodeError as e:
        print(f"Failed to parse Gemini output: {response_text}")
        return {"replyText": "I'm sorry, I couldn't understand your request properly.", "items": []}
    except Exception as e:
        print(f"Gemini API Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")


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
            continue  # Skip invalid items or raise error

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


# -------------------------------------------------
# User Settings
# -------------------------------------------------
from pydantic import BaseModel

class SettingsUpdate(BaseModel):
    language: str

@app.get("/api/user/settings")
def get_user_settings(
        user: TelegramUser = Depends(get_current_user)
):
    lang = user.language if hasattr(user, 'language') else "ru"
    return {"language": lang}

@app.post("/api/user/settings")
def update_user_settings(
        payload: SettingsUpdate,
        user: TelegramUser = Depends(get_current_user)
):
    print(f"--- UPDATE SETTINGS HIT --- User: {user.telegram_id}, New Lang: {payload.language}")
    
    # Open isolated session to perform explicit UPDATE query (bypassing Depends caching collision)
    from shared.db import SessionLocal
    db = SessionLocal()
    try:
        db.query(TelegramUser).filter(TelegramUser.id == user.id).update(
            {"language": payload.language}
        )
        db.commit()
    finally:
        db.close()
    
    print(f"--- Successfully saved lang: {payload.language} for User: {user.telegram_id}")
    return {"status": "ok", "language": payload.language}


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
