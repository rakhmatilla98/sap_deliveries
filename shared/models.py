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


# -------------------------------------------------
# Marketplace Models
# -------------------------------------------------

class Item(Base):
    __tablename__ = "items"

    item_code = Column(String, primary_key=True, index=True)
    item_name = Column(String, index=True)
    quantity = Column(Float, default=0.0)
    price = Column(Float, default=0.0)
    currency = Column(String, default="UZS")
    

    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    images = relationship("ItemImage", back_populates="item", cascade="all, delete-orphan")


class ItemImage(Base):
    __tablename__ = "item_images"

    id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String, ForeignKey("items.item_code"), index=True)
    file_path = Column(String, nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    item = relationship("Item", back_populates="images")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    
    # Link to Telegram User (who made the order)
    telegram_id = Column(Integer, index=True) 
    card_code = Column(String, nullable=True) # If we know the BP
    card_name = Column(String, nullable=True)

    doc_total = Column(Float, default=0.0)
    currency = Column(String, default="UZS")
    
    status = Column(String, default="new") # new, synced, error
    
    # SAP Sync info
    sap_doc_entry = Column(Integer, nullable=True)
    sap_doc_num = Column(String, nullable=True)
    sap_error = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    
    item_code = Column(String)
    item_name = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    line_total = Column(Float)

    order = relationship("Order", back_populates="items")


class Cart(Base):
    """Server-side cart storage"""
    __tablename__ = "carts"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, index=True, nullable=False)
    item_code = Column(String, index=True, nullable=False)
    quantity = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Unique constraint: one user can have one entry per item
    __table_args__ = (
        {'sqlite_autoincrement': True}
    )

