from pydantic import BaseModel
from datetime import datetime
from app.models.order import OrderStatus
from typing import Any

class OrderItemIn(BaseModel):
    product_id: int
    quantity:   int

class OrderCreate(BaseModel):
    items:          list[OrderItemIn]
    address_id:     int
    payment_method: str
    notes:          str | None = None

class OrderItemOut(BaseModel):
    product_id: int
    name:       str
    price:      float
    quantity:   int
    image:      str | None

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id:             int
    order_number:   str
    status:         OrderStatus
    subtotal:       float
    shipping:       float
    tax:            float
    total:          float
    payment_method: str | None
    payment_status: str
    address:        dict[str, Any]
    tracking:       list[dict]
    items:          list[OrderItemOut]
    created_at:     datetime

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class AddressCreate(BaseModel):
    label:      str = "Home"
    full_name:  str
    street:     str
    city:       str
    state:      str
    zip:        str
    country:    str = "India"
    phone:      str | None = None
    is_default: bool = False