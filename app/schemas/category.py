from datetime import datetime
from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    slug: str
    icon: str | None = None


class CategoryOut(BaseModel):
    id:            int
    name:          str
    slug:          str
    icon:          str | None
    product_count: int
    created_at:    datetime

    class Config:
        from_attributes = True