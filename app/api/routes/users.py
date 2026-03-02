from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.order import Address
from app.schemas.user import UserOut, UserUpdate
from app.schemas.order import AddressCreate
from app.api.deps import get_current_user, get_current_admin

router = APIRouter(prefix="/users", tags=["users"])


# ── Address routes — MUST come before /me to avoid route conflict ─────────────

@router.get("/me/addresses")
def get_addresses(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    addresses = db.query(Address).filter(Address.user_id == current_user.id).all()
    return [
        {
            "id":         a.id,
            "user_id":    a.user_id,
            "label":      a.label,
            "full_name":  a.full_name,
            "street":     a.street,
            "city":       a.city,
            "state":      a.state,
            "zip":        a.zip,
            "country":    a.country,
            "phone":      a.phone,
            "is_default": a.is_default,
        }
        for a in addresses
    ]


@router.post("/me/addresses", status_code=201)
def add_address(
    data:         AddressCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    # If new address is default, unset existing default
    if data.is_default:
        db.query(Address).filter(
            Address.user_id    == current_user.id,
            Address.is_default == True,
        ).update({"is_default": False})

    addr = Address(user_id=current_user.id, **data.model_dump())
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return {
        "id":         addr.id,
        "user_id":    addr.user_id,
        "label":      addr.label,
        "full_name":  addr.full_name,
        "street":     addr.street,
        "city":       addr.city,
        "state":      addr.state,
        "zip":        addr.zip,
        "country":    addr.country,
        "phone":      addr.phone,
        "is_default": addr.is_default,
    }


@router.delete("/me/addresses/{address_id}", status_code=204)
def delete_address(
    address_id:   int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    addr = db.query(Address).filter(
        Address.id      == address_id,
        Address.user_id == current_user.id,
    ).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(addr)
    db.commit()


@router.patch("/me/addresses/{address_id}/default")
def set_default_address(
    address_id:   int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    # Unset all defaults first
    db.query(Address).filter(
        Address.user_id    == current_user.id,
        Address.is_default == True,
    ).update({"is_default": False})

    # Set new default
    addr = db.query(Address).filter(
        Address.id      == address_id,
        Address.user_id == current_user.id,
    ).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")

    addr.is_default = True
    db.commit()
    return {"message": "Default address updated"}


# ── User profile routes ───────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_profile(
    data:         UserUpdate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(current_user, key, val)
    db.commit()
    db.refresh(current_user)
    return current_user


# ── Admin routes ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[UserOut])
def get_all_users(
    db:     Session = Depends(get_db),
    _admin: User    = Depends(get_current_admin),
):
    return db.query(User).all()


@router.patch("/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db:      Session = Depends(get_db),
    _admin:  User    = Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    return {"message": "User deactivated"}