# shared/models.py
import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Numeric, Float, ForeignKey
)
from sqlalchemy.orm import relationship

from shared.db import Base


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    card_code = Column(String, index=True)
    card_name = Column(String, nullable=True)
    doc_entry = Column(Integer, unique=True, index=True, nullable=False)
    document_number = Column(String, nullable=False)

    sales_manager = Column(String, nullable=True)
    date = Column(String, nullable=False)  # ISO string

    remarks = Column(String, nullable=True)
    document_total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String, nullable=True)

    approved = Column(Boolean, default=False)
    approved_at = Column(DateTime, nullable=True)

    sap_synced = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # ✅ NEW
    items = relationship(
        "DeliveryItem",
        back_populates="delivery",
        cascade="all, delete-orphan"
    )


class DeliveryItem(Base):
    __tablename__ = "delivery_items"

    id = Column(Integer, primary_key=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.id"), index=True)

    line_num = Column(Integer)
    item_code = Column(String)
    item_name = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    line_total = Column(Float)

    delivery = relationship("Delivery", back_populates="items")


class TelegramUser(Base):
    __tablename__ = "telegram_users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)

    phone_number = Column(String, nullable=True)

    card_code = Column(String, nullable=True, default="unknown")
    card_name = Column(String, nullable=True)

    role = Column(String, default="approver")  # viewer | approver

    is_active = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)

    last_sap_sync = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
