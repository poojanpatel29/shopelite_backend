from pydantic import BaseModel
from datetime import datetime
from typing import Any

class ProductBase(BaseModel):
    name:           str
    description:    str | None = None
    price:          float
    discount:       int = 0
    stock:          int = 0
    image:          str | None = None
    images:         list[str] = []
    category:       str
    tags:           list[str] = []
    specifications: dict[str, Any] = {}
    is_featured:    bool = False
    is_new:         bool = False

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class ProductOut(ProductBase):
    id:         int
    slug:       str
    rating:     float
    reviews:    int
    sold:       int
    is_active:  bool
    created_at: datetime

    class Config:
        from_attributes = True