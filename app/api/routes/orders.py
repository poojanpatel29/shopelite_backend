import random
import string
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.api.deps import get_current_admin, get_current_user
from app.core.database import get_db
from app.models.order import Address, Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["orders"])

# ── Business constants ────────────────────────────────────────────────────────
FREE_SHIPPING_THRESHOLD = 500.0
SHIPPING_COST           = 99.0
TAX_RATE                = 0.18

TRACKING_STEPS = [
    "Order Placed",
    "Processing",
    "Shipped",
    "Out for Delivery",
    "Delivered",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize_status(status: str) -> str:
    """Normalize any status string to snake_case for consistent lookup."""
    return status.lower().replace(" ", "_")


# Build lookup from both snake_case and display-name forms
STATUS_TO_IDX: dict[str, int] = {}
for _i, _step in enumerate(TRACKING_STEPS):
    STATUS_TO_IDX[_normalize_status(_step)] = _i
    STATUS_TO_IDX[_step] = _i


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_order_number() -> str:
    year = datetime.now(timezone.utc).year
    rand = "".join(random.choices(string.digits, k=6))
    return f"ORD-{year}-{rand}"


def _calculate_totals(subtotal: float) -> tuple[float, float, float]:
    shipping = 0.0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_COST
    tax      = subtotal * TAX_RATE
    return shipping, tax, subtotal + shipping + tax


def _build_address_dict(address: Address) -> dict:
    return {
        "full_name": address.full_name,
        "street":    address.street,
        "city":      address.city,
        "state":     address.state,
        "zip":       address.zip,
        "country":   address.country,
    }


def _build_initial_tracking() -> list[dict]:
    tracking = [{"status": step, "date": None, "done": False} for step in TRACKING_STEPS]
    tracking[0]["done"] = True
    tracking[0]["date"] = _now_iso()
    return tracking


def _serialize_order(o: Order) -> dict:
    return {
        "id":             o.id,
        "order_number":   o.order_number,
        "user_id":        o.user_id,
        "status":         o.status.value if hasattr(o.status, "value") else o.status,
        "subtotal":       o.subtotal,
        "shipping":       o.shipping,
        "tax":            o.tax,
        "total":          o.total,
        "payment_method": o.payment_method,
        "payment_status": o.payment_status,
        "address":        o.address  if isinstance(o.address,  dict) else {},
        "tracking":       o.tracking if isinstance(o.tracking, list) else [],
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


def _get_last_done_index(tracking: list[dict]) -> int:
    """Return the index of the last completed tracking step, or -1 if none."""
    last = -1
    for i, step in enumerate(tracking):
        if step.get("done"):
            last = i
    return last


def _process_order_items(items_in, db: Session) -> tuple[float, list[OrderItem]]:
    """Validate items, deduct stock, return (subtotal, order_items)."""
    subtotal    = 0.0
    order_items = []

    for item_in in items_in:
        product = db.query(Product).filter(
            Product.id        == item_in.product_id,
            Product.is_active.is_(True),
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

    return subtotal, order_items


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
def get_all_orders(
    db:     Session = Depends(get_db),
    _admin: User    = Depends(get_current_admin),
):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return [_serialize_order(o) for o in orders]


@router.get("/my")
def get_my_orders(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return [_serialize_order(o) for o in orders]


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
    return _serialize_order(order)


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

    subtotal, order_items = _process_order_items(data.items, db)
    shipping, tax, total  = _calculate_totals(subtotal)

    order = Order(
        order_number   = _generate_order_number(),
        user_id        = current_user.id,
        subtotal       = subtotal,
        shipping       = shipping,
        tax            = tax,
        total          = total,
        payment_method = data.payment_method,
        payment_status = "pending",
        address        = _build_address_dict(address),
        tracking       = _build_initial_tracking(),
        notes          = data.notes,
        items          = order_items,
    )

    try:
        db.add(order)
        db.commit()
        db.refresh(order)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create order") from exc

    return _serialize_order(order)


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

    new_status = data.status.value if hasattr(data.status, "value") else data.status
    new_idx    = STATUS_TO_IDX.get(_normalize_status(new_status))

    if new_idx is None:
        raise HTTPException(status_code=400, detail=f"Unknown status: {new_status}")

    tracking    = list(order.tracking or [])
    current_idx = _get_last_done_index(tracking)

    if new_idx <= current_idx:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot move order backwards. Current step: {current_idx}, requested: {new_idx}.",
        )

    if new_idx > current_idx + 1:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot skip steps. Current step: {current_idx}, requested: {new_idx}.",
        )

    now = _now_iso()
    if new_idx < len(tracking):
        tracking[new_idx]["done"] = True
        tracking[new_idx]["date"] = now

    order.tracking = tracking
    order.status   = new_status
    flag_modified(order, "tracking")

    try:
        db.commit()
        db.refresh(order)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update order status") from exc

    return _serialize_order(order)