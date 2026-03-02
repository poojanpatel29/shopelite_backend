from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.order import Order, OrderItem, Address
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderStatusUpdate
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User
import random, string
from datetime import datetime

router = APIRouter(prefix="/orders", tags=["orders"])


def generate_order_number() -> str:
    year = datetime.now().year
    rand = ''.join(random.choices(string.digits, k=6))
    return f"ORD-{year}-{rand}"


def serialize_order(o) -> dict:
    return {
        "id":             o.id,
        "order_number":   o.order_number,
        "user_id":        o.user_id,
        "status":         o.status.value if hasattr(o.status, 'value') else o.status,
        "subtotal":       o.subtotal,
        "shipping":       o.shipping,
        "tax":            o.tax,
        "total":          o.total,
        "payment_method": o.payment_method,
        "payment_status": o.payment_status,
        "address":        o.address   if isinstance(o.address,   dict) else {},
        "tracking":       o.tracking  if isinstance(o.tracking,  list) else [],
        "notes":          o.notes or "",
        "items": [
            {
                "product_id": i.product_id,
                "name":       i.name,
                "price":      i.price,
                "quantity":   i.quantity,
                "image":      i.image or "",
            }
            for i in (o.items or [])
        ],
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "updated_at": o.updated_at.isoformat() if o.updated_at else None,
    }


@router.get("")                         # ← Admin — get all orders
def get_all_orders(
    db:     Session = Depends(get_db),
    _admin: User    = Depends(get_current_admin),
):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return [serialize_order(o) for o in orders]


@router.get("/my")                      # ← User — get own orders
def get_my_orders(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    orders = db.query(Order).filter(Order.user_id == current_user.id)\
               .order_by(Order.created_at.desc()).all()
    return [serialize_order(o) for o in orders]


@router.get("/{order_id}")
def get_order(
    order_id:     int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return serialize_order(order)


@router.post("", status_code=201)
def create_order(
    data:         OrderCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    address = db.query(Address).filter(
        Address.id      == data.address_id,
        Address.user_id == current_user.id,
    ).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    subtotal    = 0.0
    order_items = []

    for item_in in data.items:
        product = db.query(Product).filter(
            Product.id        == item_in.product_id,
            Product.is_active == True,
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_in.product_id} not found")
        if product.stock < item_in.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")

        price     = product.price * (1 - product.discount / 100) if product.discount else product.price
        subtotal += price * item_in.quantity

        order_items.append(OrderItem(
            product_id = product.id,
            name       = product.name,
            price      = price,
            quantity   = item_in.quantity,
            image      = product.image,
        ))

        product.stock -= item_in.quantity
        product.sold  += item_in.quantity

    shipping = 0.0 if subtotal >= 500 else 99.0
    tax      = subtotal * 0.18
    total    = subtotal + shipping + tax

    order = Order(
        order_number   = generate_order_number(),
        user_id        = current_user.id,
        subtotal       = subtotal,
        shipping       = shipping,
        tax            = tax,
        total          = total,
        payment_method = data.payment_method,
        payment_status = "pending",
        address        = {
            "full_name": address.full_name,
            "street":    address.street,
            "city":      address.city,
            "state":     address.state,
            "zip":       address.zip,
            "country":   address.country,
        },
        tracking = [
            {"status": "Order Placed",     "date": datetime.utcnow().isoformat(), "done": True},
            {"status": "Processing",       "date": None, "done": False},
            {"status": "Shipped",          "date": None, "done": False},
            {"status": "Out for Delivery", "date": None, "done": False},
            {"status": "Delivered",        "date": None, "done": False},
        ],
        notes = data.notes,
        items = order_items,
    )

    db.add(order)
    db.commit()
    db.refresh(order)
    return serialize_order(order)


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    data:     OrderStatusUpdate,
    db:       Session = Depends(get_db),
    _admin:   User    = Depends(get_current_admin),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = data.status

    status_map = {"processing": 1, "shipped": 2, "delivered": 4}
    tracking   = order.tracking or []
    idx        = status_map.get(data.status.value if hasattr(data.status, 'value') else data.status)
    if idx and idx < len(tracking):
        tracking[idx]["done"] = True
        tracking[idx]["date"] = datetime.utcnow().isoformat()
    order.tracking = tracking

    db.commit()
    db.refresh(order)
    return serialize_order(order)