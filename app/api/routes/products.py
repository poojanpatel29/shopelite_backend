from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.api.deps import get_current_admin
from app.models.user import User

router = APIRouter(prefix="/products", tags=["products"])


def serialize_product(p: Product) -> dict:
    return {
        "id":             p.id,
        "name":           p.name,
        "slug":           p.slug or "",
        "description":    p.description or "",
        "price":          p.price,
        "discount":       p.discount or 0,
        "stock":          p.stock or 0,
        "rating":         p.rating or 0.0,
        "reviews":        p.reviews or 0,
        "sold":           p.sold or 0,
        "image":          p.image or "",
        "images":         p.images  if isinstance(p.images,  list) else [],
        "category":       p.category or "",
        "tags":           p.tags    if isinstance(p.tags,    list) else [],
        "specifications": p.specifications if isinstance(p.specifications, dict) else {},
        "is_featured":    p.is_featured or False,
        "is_new":         p.is_new      or False,
        "is_active":      p.is_active   if p.is_active is not None else True,
        "created_at":     p.created_at.isoformat() if p.created_at else None,
    }


# ── Public routes (no auth needed) ───────────────────────────────────────────

@router.get("")                         # ← no response_model
def get_products(
    db:        Session = Depends(get_db),
    page:      int     = Query(1, ge=1),
    per_page:  int     = Query(12, ge=1, le=100),
    category:  str     = Query(None),
    search:    str     = Query(None),
    min_price: float   = Query(None),
    max_price: float   = Query(None),
    sort_by:   str     = Query("featured"),
    in_stock:  bool    = Query(False),
):
    query = db.query(Product).filter(Product.is_active == True)

    if category:              query = query.filter(Product.category == category)
    if search:                query = query.filter(Product.name.ilike(f"%{search}%"))
    if min_price is not None: query = query.filter(Product.price >= min_price)
    if max_price is not None: query = query.filter(Product.price <= max_price)
    if in_stock:              query = query.filter(Product.stock > 0)

    if sort_by == "price-asc":    query = query.order_by(Product.price.asc())
    elif sort_by == "price-desc": query = query.order_by(Product.price.desc())
    elif sort_by == "rating":     query = query.order_by(Product.rating.desc())
    elif sort_by == "newest":     query = query.order_by(Product.created_at.desc())
    else:                         query = query.order_by(Product.is_featured.desc())

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items":    [serialize_product(p) for p in items],
        "total":    total,
        "page":     page,
        "per_page": per_page,
    }


@router.get("/{product_id}")            # ← no response_model
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_product(product)


# ── Admin routes ──────────────────────────────────────────────────────────────

@router.post("", status_code=201)       # ← no response_model
def create_product(
    data:   ProductCreate,
    db:     Session = Depends(get_db),
    _admin: User    = Depends(get_current_admin),
):
    slug = data.name.lower()
    slug = ''.join(c if c.isalnum() or c == ' ' else ' ' for c in slug)
    slug = '-'.join(slug.split())

    product = Product(**data.model_dump(), slug=slug)
    db.add(product)
    db.commit()
    db.refresh(product)
    return serialize_product(product)


@router.put("/{product_id}")            # ← no response_model
def update_product(
    product_id: int,
    data:       ProductUpdate,
    db:         Session = Depends(get_db),
    _admin:     User    = Depends(get_current_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(product, key, val)
    db.commit()
    db.refresh(product)
    return serialize_product(product)


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db:         Session = Depends(get_db),
    _admin:     User    = Depends(get_current_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    db.commit()