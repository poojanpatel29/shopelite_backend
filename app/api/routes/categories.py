from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.product import Category, Product
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def get_all_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.name).all()

    # Sync product_count with actual count before returning
    for cat in categories:
        cat.product_count = (
            db.query(func.count(Product.id))
            .filter(Product.category_id == cat.id, Product.is_active.is_(True))
            .scalar()
        )

    return categories


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(
    data:   CategoryCreate,
    db:     Session = Depends(get_db),
    _admin: User    = Depends(get_current_admin),
):
    existing = db.query(Category).filter(Category.slug == data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this slug already exists")

    category = Category(
        name          = data.name,
        slug          = data.slug,
        icon          = data.icon,
        product_count = 0,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db:          Session  = Depends(get_db),
    _admin:      User     = Depends(get_current_admin),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()