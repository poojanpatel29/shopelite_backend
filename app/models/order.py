from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class OrderStatus(str, enum.Enum):
    pending          = "pending" 
    order_placed     = "order_placed"
    processing       = "processing"
    shipped          = "shipped"
    out_for_delivery = "out_for_delivery"
    delivered        = "delivered"
    cancelled        = "cancelled"

class Order(Base):
    __tablename__ = "orders"

    id             = Column(Integer, primary_key=True, index=True)
    order_number   = Column(String(50), unique=True, index=True)  # ORD-2024-001
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    status         = Column(Enum(OrderStatus), default=OrderStatus.pending)
    subtotal       = Column(Float, nullable=False)
    shipping       = Column(Float, default=0.0)
    tax            = Column(Float, default=0.0)
    total          = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=True)
    payment_status = Column(String(50), default="pending")
    address        = Column(JSON, nullable=False)   # snapshot of address at order time
    tracking       = Column(JSON, default=[])
    notes          = Column(String(500), nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), onupdate=func.now())

    user   = relationship("User",      back_populates="orders")
    items  = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id         = Column(Integer, primary_key=True, index=True)
    order_id   = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name       = Column(String(255), nullable=False)   # snapshot of product name
    price      = Column(Float, nullable=False)         # snapshot of price at order time
    quantity   = Column(Integer, nullable=False)
    image      = Column(String(500), nullable=True)

    order   = relationship("Order",   back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Address(Base):
    __tablename__ = "addresses"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    label      = Column(String(50), default="Home")
    full_name  = Column(String(100), nullable=False)
    street     = Column(String(255), nullable=False)
    city       = Column(String(100), nullable=False)
    state      = Column(String(100), nullable=False)
    zip        = Column(String(20),  nullable=False)
    country    = Column(String(100), default="India")
    phone      = Column(String(20),  nullable=True)
    is_default = Column(Boolean, default=False)

    user = relationship("User", back_populates="addresses")


class CartItem(Base):
    __tablename__ = "cart_items"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity   = Column(Integer, default=1)

    user    = relationship("User",    back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


class Wishlist(Base):
    __tablename__ = "wishlist"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    user    = relationship("User",    back_populates="wishlist")
    product = relationship("Product", back_populates="wishlist")