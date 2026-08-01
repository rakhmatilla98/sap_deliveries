# shared/schemas.py
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class DeliveryItemOut(BaseModel):
    line_num: int
    item_code: str
    item_name: str
    quantity: float
    price: float
    line_total: float

    class Config:
        from_attributes = True


class DeliveryOut(BaseModel):
    id: int
    doc_entry: int
    document_number: str
    sales_manager: str | None
    date: str
    remarks: str | None
    document_total_amount: Decimal
    approved: bool
    items: list[DeliveryItemOut] = []
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryOut(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[DeliveryOut]


# -------------------------------------------------
# Marketplace Schemas
# -------------------------------------------------

class ItemCategoryOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    sort_order: int
    image_url: str | None = None

    class Config:
        from_attributes = True


class ItemCategoryIn(BaseModel):
    name: str
    description: str | None = None
    sort_order: int = 0
    image_url: str | None = None


class ItemOut(BaseModel):
    item_code: str
    item_name: str
    description: str | None = None
    quantity: float
    price: float
    currency: str
    image_url: str | None = None
    image_urls: list[str] = []
    category: ItemCategoryOut | None = None

    class Config:
        from_attributes = True


class CartItem(BaseModel):
    item_code: str
    quantity: float


class OrderIn(BaseModel):
    items: list[CartItem]


# Cart Schemas
class CartItemIn(BaseModel):
    item_code: str
    quantity: int = 1


class CartItemOut(BaseModel):
    item_code: str
    item_name: str
    quantity: int
    price: float
    currency: str
    image_url: str | None = None
    line_total: float
    
    class Config:
        from_attributes = True


class CartUpdateIn(BaseModel):
    quantity: int


class ItemCategoryUpdate(BaseModel):
    item_codes: list[str]
    category_id: int | None = None


