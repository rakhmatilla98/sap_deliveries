# shared/schemas.py
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class DeliveryOut(BaseModel):
    id: int
    doc_entry: int
    document_number: str
    sales_manager: str | None
    date: str
    remarks: str | None
    document_total_amount: Decimal
    approved: bool
    created_at: datetime

    class Config:
        orm_mode = True
