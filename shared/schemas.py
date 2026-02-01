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
