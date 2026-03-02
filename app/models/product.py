from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), unique=True, nullable=False)
    slug          = Column(String(100), unique=True, nullable=False)
    icon          = Column(String(10),  nullable=True)
    product_count = Column(Integer, default=0)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    products = relationship("Product", back_populates="category_rel")


class Product(Base):
    __tablename__ = "products"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(255), nullable=False, index=True)
    slug        = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    price       = Column(Float, nullable=False)
    discount    = Column(Integer, default=0)           # percentage
    stock       = Column(Integer, default=0)
    rating      = Column(Float, default=0.0)
    reviews     = Column(Integer, default=0)
    sold        = Column(Integer, default=0)
    image       = Column(String(500), nullable=True)
    images      = Column(JSON, default=[])             # list of URLs
    category    = Column(String(100), nullable=False)
    tags        = Column(JSON, default=[])
    specifications = Column(JSON, default={})
    is_featured = Column(Boolean, default=False)
    is_new      = Column(Boolean, default=False)
    is_active   = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    category_rel = relationship("Category", back_populates="products")
    order_items  = relationship("OrderItem", back_populates="product")
    cart_items   = relationship("CartItem",  back_populates="product")
    wishlist     = relationship("Wishlist",  back_populates="product")