from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    user  = "user"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(255), unique=True, index=True, nullable=False)
    phone      = Column(String(20), nullable=True)
    password   = Column(String(255), nullable=False)         # argon2 hash
    role       = Column(Enum(UserRole), default=UserRole.user)
    avatar     = Column(String(500), nullable=True)
    is_active  = Column(Boolean, default=True)
    is_verified= Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    orders    = relationship("Order",   back_populates="user")
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    cart_items= relationship("CartItem",back_populates="user", cascade="all, delete-orphan")
    wishlist  = relationship("Wishlist",back_populates="user", cascade="all, delete-orphan")